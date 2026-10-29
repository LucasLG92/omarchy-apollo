// SPDX-License-Identifier: GPL-2.0
/* Test-only APR DMA lifecycle audit. No APR packets or audio playback.
 * Synthetic detached OF nodes copy the real client's IOMMU specifier, so
 * allocations use the existing domain, without inventing a hardware stream.
 * This module neither unbinds the real service nor applies an OF changeset.
 */
#include <linux/device.h>
#include <linux/dma-mapping.h>
#include <linux/iommu.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/slab.h>
#include <linux/sizes.h>
#include <linux/soc/qcom/apr.h>

#define ROUNDS 8
struct audit_device {
	struct apr_device apr;
	bool fail_probe;
	bool no_iommu;
	unsigned int probes;
};
static struct device *real_dev;
static struct device_driver *real_driver;
static struct iommu_group *real_group;
static struct iommu_domain *real_domain;
static bool driver_registered;
static bool passed;
static int failures, created, released, probes, removes, allocations, pages;
static int failed_probes, plain_probes, rebinds, group_baseline;
static int prebind_iommu_devices, prebind_plain_devices;
module_param(passed, bool, 0444);
module_param(failures, int, 0444);
module_param(created, int, 0444);
module_param(released, int, 0444);
module_param(probes, int, 0444);
module_param(removes, int, 0444);
module_param(allocations, int, 0444);
module_param(pages, int, 0444);
module_param(failed_probes, int, 0444);
module_param(plain_probes, int, 0444);
module_param(rebinds, int, 0444);
module_param(group_baseline, int, 0444);
module_param(prebind_iommu_devices, int, 0444);
module_param(prebind_plain_devices, int, 0444);

static int count_member(struct device *dev, void *data)
{
	(*(int *)data)++;
	return 0;
}

static int group_count(void)
{
	int count = 0;
	int ret = iommu_group_for_each_dev(real_group, &count, count_member);
	return ret ? ret : count;
}

static int audit_buffers(struct device *dev)
{
	const size_t sizes[] = { PAGE_SIZE, SZ_64K, SZ_256K };
	unsigned int i;
	for (i = 0; i < ARRAY_SIZE(sizes); i++) {
		dma_addr_t dma;
		void *cpu = dma_alloc_coherent(dev, sizes[i], &dma, GFP_KERNEL);
		size_t offset;
		bool bad = false;
		if (!cpu)
			return -ENOMEM;
		allocations++;
		memset(cpu, 0xa5, sizes[i]);
		if (memchr_inv(cpu, 0xa5, sizes[i]))
			bad = true;
		for (offset = 0; offset < sizes[i]; offset += PAGE_SIZE) {
			if (!iommu_iova_to_phys(real_domain, dma + offset))
				bad = true;
			pages++;
		}
		dma_free_coherent(dev, sizes[i], cpu, dma);
		/* Verify every mapping disappeared, not just the first page. */
		for (offset = 0; offset < sizes[i]; offset += PAGE_SIZE)
			if (iommu_iova_to_phys(real_domain, dma + offset))
				bad = true;
		if (bad)
			return -EIO;
	}
	return 0;
}

static int audit_probe(struct apr_device *apr)
{
	struct audit_device *test = container_of(apr, struct audit_device, apr);
	int ret;
	test->probes++;
	probes++;
	if (test->no_iommu) {
		plain_probes++;
		if (apr->dev.iommu_group || iommu_get_domain_for_dev(&apr->dev)) {
			failures++;
			return -EINVAL;
		}
		return 0;
	}
	if (apr->dev.iommu_group != real_group ||
	    iommu_get_domain_for_dev(&apr->dev) != real_domain ||
	    group_count() != group_baseline + 1) {
		failures++;
		return -EINVAL;
	}
	ret = audit_buffers(&apr->dev);
	if (ret) {
		failures++;
		return ret;
	}
	if (test->fail_probe) {
		failed_probes++;
		return -ENODEV; /* Intentional failure exercises driver-core unwind. */
	}
	return 0;
}

static void audit_remove(struct apr_device *apr)
{
	removes++;
}

static const struct of_device_id audit_match[] = {
	{ .compatible = "apollo,apr-dma-audit" }, { }
};
static struct apr_driver audit_driver = {
	.probe = audit_probe,
	.remove = audit_remove,
	.driver = {
		.name = "apollo-apr-dma-audit",
		.of_match_table = audit_match,
		.probe_type = PROBE_FORCE_SYNCHRONOUS,
	},
};

static void audit_release(struct device *dev)
{
	struct audit_device *test = container_of(to_apr_device(dev),
						struct audit_device, apr);
	of_node_put(dev->of_node);
	kfree(test);
	released++;
	/* A pending release prevents rmmod from freeing this callback's code. */
	module_put(THIS_MODULE);
}

static int add_property(struct device_node *np, const char *name,
			const void *value, int len)
{
	struct property *prop = kzalloc(sizeof(*prop), GFP_KERNEL);
	int ret;
	if (!prop)
		return -ENOMEM;
	prop->name = kstrdup(name, GFP_KERNEL);
	prop->value = kmemdup(value, len, GFP_KERNEL);
	prop->length = len;
	if (!prop->name || (len && !prop->value)) {
		ret = -ENOMEM;
		goto free;
	}
	of_property_set_flag(prop, OF_DYNAMIC);
	ret = of_add_property(np, prop);
	if (!ret)
		return 0;
free:
	kfree(prop->value);
	kfree(prop->name);
	kfree(prop);
	return ret;
}

static int run_one(unsigned int round, unsigned int mode)
{
	struct of_changeset changes;
	struct device_node *np;
	struct audit_device *test = NULL;
	const void *spec;
	char name[80];
	int len, ret = 0;
	bool added = false;
	static const char compatible[] = "apollo,apr-dma-audit";
	of_changeset_init(&changes);
	snprintf(name, sizeof(name), "apollo-apr-dma-audit-%u-%u", round, mode);
	np = of_changeset_create_node(&changes, real_dev->of_node->parent, name);
	if (!np) {
		ret = -ENOMEM;
		goto destroy;
	}
	np->name = kbasename(np->full_name);
	ret = add_property(np, "compatible", compatible, sizeof(compatible));
	if (ret)
		goto put_node;
	if (mode != 2) {
		spec = of_get_property(real_dev->of_node, "iommus", &len);
		if (!spec || len <= 0) {
			ret = -ENODEV;
			goto put_node;
		}
		ret = add_property(np, "iommus", spec, len);
		if (ret)
			goto put_node;
		if (of_property_read_bool(real_dev->of_node, "dma-coherent")) {
			ret = add_property(np, "dma-coherent", NULL, 0);
			if (ret)
				goto put_node;
		}
	}
	test = kzalloc(sizeof(*test), GFP_KERNEL);
	if (!test) {
		ret = -ENOMEM;
		goto put_node;
	}
	test->fail_probe = mode == 1;
	test->no_iommu = mode == 2;
	test->apr.svc.id = -1; /* Not inserted into the router's nonnegative IDR. */
	test->apr.svc_id = U16_MAX;
	test->apr.domain_id = U16_MAX;
	spin_lock_init(&test->apr.svc.lock);
	strscpy(test->apr.name, "dma-audit", sizeof(test->apr.name));
	test->apr.dev.parent = real_dev->parent;
	test->apr.dev.bus = &aprbus;
	test->apr.dev.of_node = of_node_get(np);
	test->apr.dev.release = audit_release;
	device_initialize(&test->apr.dev);
	__module_get(THIS_MODULE);
	created++;
	ret = dev_set_name(&test->apr.dev, "%s", name);
	if (ret)
		goto put_device;
	if (driver_registered) {
		apr_driver_unregister(&audit_driver);
		driver_registered = false;
	}
	ret = device_add(&test->apr.dev);
	if (ret)
		goto put_device;
	added = true;
	/* The new bus notifier must configure the group BEFORE any driver bind. */
	if (test->probes || test->apr.dev.driver ||
	    (mode == 2 ? test->apr.dev.iommu_group != NULL :
	     (test->apr.dev.iommu_group != real_group ||
	      iommu_get_domain_for_dev(&test->apr.dev) != real_domain))) {
		ret = -EINVAL;
		goto put_device;
	}
	if (mode == 2)
		prebind_plain_devices++;
	else
		prebind_iommu_devices++;
	ret = apr_driver_register(&audit_driver);
	if (ret)
		goto put_device;
	driver_registered = true;
	if (test->probes != 1 ||
	    (mode == 1 ? test->apr.dev.driver != NULL :
	     test->apr.dev.driver != &audit_driver.driver)) {
		ret = -EINVAL;
		goto put_device;
	}
	if (mode == 0) {
		/* Only our private driver is unregistered; q6core stays bound. */
		apr_driver_unregister(&audit_driver);
		driver_registered = false;
		if (test->apr.dev.driver) {
			ret = -EBUSY;
			goto put_device;
		}
		ret = apr_driver_register(&audit_driver);
		if (ret)
			goto put_device;
		driver_registered = true;
		if (test->probes != 2 || test->apr.dev.driver != &audit_driver.driver) {
			ret = -EINVAL;
			goto put_device;
		}
		rebinds++;
	}
put_device:
	if (added)
		device_del(&test->apr.dev);
	put_device(&test->apr.dev);
put_node:
	of_node_put(np);
destroy:
	/* Never applied: no live device-tree nodes were added or removed. */
	of_changeset_destroy(&changes);
	if (group_count() != group_baseline ||
	    real_dev->driver != real_driver ||
	    iommu_get_domain_for_dev(real_dev) != real_domain)
		ret = -EIO;
	return ret;
}

static int __init audit_init(void)
{
	unsigned int i, mode;
	int ret;
	real_dev = bus_find_device_by_name(&aprbus, NULL, "aprsvc:service:4:3");
	if (!real_dev)
		return -ENODEV;
	real_driver = real_dev->driver;
	real_group = iommu_group_get(real_dev);
	real_domain = iommu_get_domain_for_dev(real_dev);
	if (!real_driver || strcmp(real_driver->name, "qcom-q6core") ||
	    !real_dev->of_node || !real_group || !real_domain) {
		ret = -ENODEV;
		goto early_error;
	}
	group_baseline = group_count();
	if (group_baseline < 1) {
		ret = -EINVAL;
		goto early_error;
	}
	ret = apr_driver_register(&audit_driver);
	if (ret)
		goto early_error;
	driver_registered = true;
	for (i = 0; i < ROUNDS && !failures; i++) {
		for (mode = 0; mode < 3 && !failures; mode++) {
			ret = run_one(i, mode);
			if (ret)
				failures++;
		}
	}
	if (driver_registered) {
		apr_driver_unregister(&audit_driver);
		driver_registered = false;
	}
	if (created != 24 || released != created || probes != 32 || removes != 24 ||
	    allocations != 72 || pages != 1944 || failed_probes != 8 ||
	    plain_probes != 8 || rebinds != 8 || prebind_iommu_devices != 16 ||
	    prebind_plain_devices != 8 || group_count() != group_baseline)
		failures++;
	passed = !failures;
	pr_info("apollo-apr-dma-audit: passed=%d failures=%d devices=%d/%d probes=%d allocations=%d pages=%d\n",
		passed, failures, released, created, probes, allocations, pages);
	/* Remain loaded on a test failure, retaining callbacks if refs linger. */
	return 0;
early_error:
	if (real_group)
		iommu_group_put(real_group);
	put_device(real_dev);
	return ret;
}

static void __exit audit_exit(void)
{
	iommu_group_put(real_group);
	put_device(real_dev);
}
module_init(audit_init);
module_exit(audit_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Silent APR DMA lifetime audit; no firmware traffic");
