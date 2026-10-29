#!/bin/sh
# Diagnostic instance only; no device power, driver or I2C writes.
set -eu
ROOT=/sys/kernel/tracing
mkdir -p "$ROOT"
if [ ! -d "$ROOT/events/i2c" ]; then mount -t tracefs tracefs "$ROOT"; fi
TRACE="$ROOT/instances/apollo-focus"
mkdir "$TRACE"
echo 0 > "$TRACE/tracing_on"
echo nop > "$TRACE/current_tracer"
echo 1024 > "$TRACE/buffer_size_kb"
echo mono > "$TRACE/trace_clock"
META=/run/apollo-focus-trace-meta
mkdir "$META"
for event in i2c_write i2c_result; do
    path="$TRACE/events/i2c/$event"
    cat "$path/format" > "$META/$event-format.txt"
    grep -q 'field:int adapter_nr;' "$path/format"
    if [ "$event" = i2c_write ]; then
        grep -q 'addr;' "$path/format"
        echo 'adapter_nr == 20 && addr == 12' > "$path/filter"
    else
        echo 'adapter_nr == 20' > "$path/filter"
    fi
    cat "$path/filter" > "$META/$event-filter.txt"
    echo 1 > "$path/enable"
done
for event in regulator_enable regulator_enable_complete regulator_disable regulator_disable_complete; do
    path="$TRACE/events/regulator/$event"
    cat "$path/format" > "$META/$event-format.txt"
    echo 'name == "vreg_l7p" || name == "vreg_l1c_1p8" || name == "vreg_l6p"' > "$path/filter"
    cat "$path/filter" > "$META/$event-filter.txt"
    echo 1 > "$path/enable"
done
for event in rpm_resume rpm_suspend rpm_return_int rpm_status; do
    path="$TRACE/events/rpm/$event"
    cat "$path/format" > "$META/$event-format.txt"
    echo 'name == "20-000c" || name == "ac4f000.cci"' > "$path/filter"
    cat "$path/filter" > "$META/$event-filter.txt"
    echo 1 > "$path/enable"
done
echo 1 > "$TRACE/tracing_on"
echo APOLLO_FOCUS_TRACE_EARLY > "$TRACE/trace_marker"
echo APOLLO_FOCUS_TRACE_SETUP_OK > /run/apollo-focus-trace-setup
echo APOLLO_FOCUS_TRACE_SETUP_OK
