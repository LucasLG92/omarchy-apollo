// SPDX-License-Identifier: GPL-2.0
/* Diagnostic-only supply A/B test. No I2C, firmware or EEPROM writes here. */
#include <linux/device.h>
#include <linux/delay.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of.h>
#include <linux/pm_runtime.h>
#include <linux/regulator/consumer.h>

static struct regulator *rail;
static struct device *lens_dev;
static char *target = "20-000c";
static bool enabled;
static int voltage_uv;
module_param(target, charp, 0444);
module_param(voltage_uv, int, 0444);

static int set_supply(const char *value, const struct kernel_param *param)
{
	bool wanted;
	bool pm_disabled = false;
	int ret;
	if (!rail || !lens_dev)
		return -EAGAIN;
	ret = kstrtobool(value, &wanted);
	if (ret)
		return ret;
	device_lock(lens_dev);
	/* Keep the media graph intact. Only change auxiliary power while the
	 * matched driver is suspended, without users, with runtime PM blocked.
	 * The original unbound diagnostic path remains supported as well.
	 */
	if (lens_dev->driver) {
		if (strcmp(lens_dev->driver->name, "ak7375")) {
			ret = -EBUSY;
			goto unlock;
		}
		pm_runtime_disable(lens_dev);
		pm_disabled = true;
		if (!pm_runtime_status_suspended(lens_dev) ||
		    atomic_read(&lens_dev->power.usage_count)) {
			ret = -EBUSY;
			goto unlock;
		}
	}
	if (wanted == enabled) {
		ret = 0;
		goto unlock;
	}
	if (wanted) {
		if (regulator_get_voltage(rail) != 2800000) {
			ret = -ERANGE;
			goto unlock;
		}
		ret = regulator_enable(rail);
		if (!ret) {
			enabled = true;
			__module_get(THIS_MODULE); /* Cannot unload while holding power. */
			usleep_range(10000, 11000);
		}
	} else {
		ret = regulator_disable(rail);
		if (!ret) {
			enabled = false;
			module_put(THIS_MODULE);
		}
	}
unlock:
	if (pm_disabled)
		pm_runtime_enable(lens_dev);
	device_unlock(lens_dev);
	return ret;
}
static const struct kernel_param_ops supply_ops = {
	.set = set_supply,
	.get = param_get_bool,
};
module_param_cb(enabled, &supply_ops, &enabled, 0600);

static bool clear_error;
static int error_clear_requests;
module_param(error_clear_requests, int, 0444);
static int reset_runtime_error(const char *value, const struct kernel_param *param)
{
	bool wanted;
	int ret;
	if (!lens_dev)
		return -EAGAIN;
	ret = kstrtobool(value, &wanted);
	if (ret || !wanted)
		return ret ? ret : -EINVAL;
	device_lock(lens_dev);
	/* Retry only the failed, fully unwound resume on this specific client.
	 * No driver rebind or live media-graph change while capture is active.
	 */
	if (!lens_dev->driver || strcmp(lens_dev->driver->name, "ak7375") ||
	    !pm_runtime_status_suspended(lens_dev) ||
	    atomic_read(&lens_dev->power.usage_count) ||
	    lens_dev->power.runtime_error != -ENXIO) {
		ret = -EBUSY;
		goto unlock;
	}
	pm_runtime_disable(lens_dev);
	if (atomic_read(&lens_dev->power.usage_count)) {
		ret = -EBUSY;
	} else {
		ret = pm_runtime_set_suspended(lens_dev);
		if (!ret)
			error_clear_requests++;
	}
	pm_runtime_enable(lens_dev);
unlock:
	device_unlock(lens_dev);
	return ret;
}
static const struct kernel_param_ops error_ops = {
	.set = reset_runtime_error,
	.get = param_get_bool,
};
module_param_cb(clear_error, &error_ops, &clear_error, 0600);

static int __init audit_init(void)
{
	int ret;
	lens_dev = bus_find_device_by_name(&i2c_bus_type, NULL, target);
	if (!lens_dev)
		return -ENODEV;
	if (!of_device_is_compatible(lens_dev->of_node, "asahi-kasei,ak7377") ||
	    !lens_dev->driver || strcmp(lens_dev->driver->name, "ak7375")) {
		ret = -ENODEV;
		goto put_device;
	}
	/* Board-defined 2.8-V L6; no voltage is programmed by this test. */
	rail = regulator_get(NULL, "vreg_l6p");
	if (IS_ERR(rail)) {
		ret = PTR_ERR(rail);
		rail = NULL;
		goto put_device;
	}
	voltage_uv = regulator_get_voltage(rail);
	if (voltage_uv != 2800000 || regulator_is_enabled(rail) != 0) {
		ret = -EBUSY;
		regulator_put(rail);
		rail = NULL;
		goto put_device;
	}
	return 0;
put_device:
	put_device(lens_dev);
	lens_dev = NULL;
	return ret;
}
static void __exit audit_exit(void)
{
	/* An enabled supply pins the module until the helper disables it. */
	regulator_put(rail);
	put_device(lens_dev);
}
module_init(audit_init);
module_exit(audit_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Apollo temporary L6 supply test; standard regulator API only");
