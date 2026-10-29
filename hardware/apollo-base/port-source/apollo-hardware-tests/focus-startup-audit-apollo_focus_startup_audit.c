// SPDX-License-Identifier: GPL-2.0
/* Temporary standard-supply hold for AK7377 startup timing observations. */
#include <linux/device.h>
#include <linux/delay.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/pm_runtime.h>
#include <linux/regulator/consumer.h>
static struct device *lens;
static struct regulator *vdd, *vio;
static bool held, clear_error;
static bool vdd_on, vio_on;
static int error_clears;
module_param(error_clears, int, 0444);
static int hold_set(const char *value, const struct kernel_param *param)
{
	bool wanted;
	int ret;
	if (!lens || !vdd || !vio)
		return -EAGAIN;
	ret = kstrtobool(value, &wanted);
	if (ret)
		return ret;
	device_lock(lens);
	pm_runtime_disable(lens);
	if (!lens->driver || strcmp(lens->driver->name, "ak7375") ||
	    !pm_runtime_status_suspended(lens) ||
	    atomic_read(&lens->power.usage_count)) {
		ret = -EBUSY;
		goto out;
	}
	if ((wanted && vdd_on && vio_on) || (!wanted && !vdd_on && !vio_on)) {
		ret = 0;
		goto out;
	}
	if (wanted) {
		if (regulator_get_voltage(vdd) != 2800000 ||
		    regulator_get_voltage(vio) != 1800000) {
			ret = -ERANGE;
			goto out;
		}
		if (!vdd_on) {
			ret = regulator_enable(vdd);
			if (ret)
				goto out;
			vdd_on = true;
			if (!held) { held = true; __module_get(THIS_MODULE); }
			usleep_range(10000, 11000);
		}
		if (!vio_on) {
			ret = regulator_enable(vio);
			if (ret)
				goto out;
			vio_on = true;
		}
		usleep_range(10000, 11000);
	} else {
		if (vio_on) {
			ret = regulator_disable(vio);
			if (ret)
				goto out;
			vio_on = false;
		}
		if (vdd_on) {
			ret = regulator_disable(vdd);
			if (ret)
				goto out;
			vdd_on = false;
		}
		held = false;
		module_put(THIS_MODULE);
	}
	ret = 0;
out:
	pm_runtime_enable(lens);
	device_unlock(lens);
	return ret;
}
static const struct kernel_param_ops hold_ops = { .set = hold_set, .get = param_get_bool };
module_param_cb(held, &hold_ops, &held, 0600);
static int clear_set(const char *value, const struct kernel_param *param)
{
	bool wanted;
	int ret;
	if (!lens)
		return -EAGAIN;
	ret = kstrtobool(value, &wanted);
	if (ret || !wanted)
		return ret ? ret : -EINVAL;
	device_lock(lens);
	pm_runtime_disable(lens);
	if (!lens->driver || strcmp(lens->driver->name, "ak7375") ||
	    !pm_runtime_status_suspended(lens) ||
	    atomic_read(&lens->power.usage_count) || lens->power.runtime_error != -ENXIO) {
		ret = -EBUSY;
	} else {
		ret = pm_runtime_set_suspended(lens);
		if (!ret)
			error_clears++;
	}
	pm_runtime_enable(lens);
	device_unlock(lens);
	return ret;
}
static const struct kernel_param_ops clear_ops = { .set = clear_set, .get = param_get_bool };
module_param_cb(clear_error, &clear_ops, &clear_error, 0600);
static int __init audit_init(void)
{
	int ret;
	lens = bus_find_device_by_name(&i2c_bus_type, NULL, "20-000c");
	if (!lens)
		return -ENODEV;
	if (!of_device_is_compatible(lens->of_node, "asahi-kasei,ak7377")) {
		ret = -ENODEV;
		goto put_device;
	}
	vdd = regulator_get(NULL, "vreg_l7p");
	if (IS_ERR(vdd)) { ret = PTR_ERR(vdd); vdd = NULL; goto put_device; }
	vio = regulator_get(NULL, "vreg_l1c_1p8");
	if (IS_ERR(vio)) { ret = PTR_ERR(vio); vio = NULL; goto put_vdd; }
	if (regulator_get_voltage(vdd) != 2800000 || regulator_get_voltage(vio) != 1800000) {
		ret = -ERANGE;
		regulator_put(vio);
		goto put_vdd;
	}
	return 0;
put_vdd:
	regulator_put(vdd);
put_device:
	put_device(lens);
	lens = NULL;
	return ret;
}
static void __exit audit_exit(void)
{
	regulator_put(vio);
	regulator_put(vdd);
	put_device(lens);
}
module_init(audit_init);
module_exit(audit_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Apollo temporary AK7377 supply timing diagnostic, no firmware");
