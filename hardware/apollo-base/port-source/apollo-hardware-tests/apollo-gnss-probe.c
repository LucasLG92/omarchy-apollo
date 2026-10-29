/* Bounded LOC session. Coordinates are checked but never printed or saved. */
#include <libqmi-glib.h>
#include <libqrtr-glib.h>
#include <glib-unix.h>
#include <math.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    GMainLoop *loop;
    QrtrBus *bus;
    QmiDevice *device;
    QmiClientLoc *loc;
    guint seconds, sv_reports, position_reports, fixes, coordinate_reports, max_satellites;
    gboolean started, stopping, mode_ack, mode_ind, standalone;
} State;
static void begin_session(State *s);
static gboolean finish(gpointer user_data);
static void failed(State *s, const char *step, GError *error) {
    g_print("error step=%s message=%s\n", step, error ? error->message : "QMI rejected request");
    g_clear_error(&error);
    g_main_loop_quit(s->loop);
}
static void position(QmiClientLoc *client, QmiIndicationLocPositionReportOutput *output, State *s) {
    QmiLocSessionStatus status = QMI_LOC_SESSION_STATUS_GENERAL_FAILURE;
    gdouble latitude, longitude;
    gfloat uncertainty = -1;
    GArray *used = NULL;
    QmiLocTechnologyUsed technology = 0;
    gboolean coordinates;
    (void)client;
    s->position_reports++;
    qmi_indication_loc_position_report_output_get_session_status(output, &status, NULL);
    coordinates = qmi_indication_loc_position_report_output_get_latitude(output, &latitude, NULL) &&
        qmi_indication_loc_position_report_output_get_longitude(output, &longitude, NULL) &&
        isfinite(latitude) && isfinite(longitude) && latitude >= -90 && latitude <= 90 &&
        longitude >= -180 && longitude <= 180;
    qmi_indication_loc_position_report_output_get_horizontal_uncertainty_circular(output, &uncertainty, NULL);
    qmi_indication_loc_position_report_output_get_satellites_used(output, &used, NULL);
    qmi_indication_loc_position_report_output_get_technology_used(output, &technology, NULL);
    if (status == QMI_LOC_SESSION_STATUS_SUCCESS && coordinates) {
        s->coordinate_reports++;
        if (used && used->len >= 3) s->fixes++;
    }
    g_print("position status=%s coordinates_valid=%d uncertainty_m=%.2f satellites_used=%u technology_mask=%u\n",
            qmi_loc_session_status_get_string(status), coordinates, uncertainty, used ? used->len : 0, (guint)technology);
}
static void satellites(QmiClientLoc *client, QmiIndicationLocGnssSvInfoOutput *output, State *s) {
    GArray *list = NULL;
    gfloat maximum = 0;
    guint signals = 0;
    (void)client;
    s->sv_reports++;
    if (qmi_indication_loc_gnss_sv_info_output_get_list(output, &list, NULL) && list) {
        s->max_satellites = MAX(s->max_satellites, list->len);
        for (guint i = 0; i < list->len; i++) {
            QmiIndicationLocGnssSvInfoOutputListElement *sv = &g_array_index(list, QmiIndicationLocGnssSvInfoOutputListElement, i);
            if (sv->signal_to_noise_ratio_bhz > 0) signals++;
            maximum = MAX(maximum, sv->signal_to_noise_ratio_bhz);
        }
    }
    g_print("satellites total=%u with_signal=%u max_cno=%.2f\n", list ? list->len : 0, signals, maximum);
}
static void engine(QmiClientLoc *client, QmiIndicationLocEngineStateOutput *output, State *s) {
    QmiLocEngineState value;
    (void)client; (void)s;
    if (qmi_indication_loc_engine_state_output_get_engine_state(output, &value, NULL))
        g_print("engine state=%s\n", qmi_loc_engine_state_get_string(value));
}
static void stopped(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    QmiMessageLocStopOutput *output = qmi_client_loc_stop_finish(QMI_CLIENT_LOC(object), result, &error);
    gboolean ok = output && qmi_message_loc_stop_output_get_result(output, &error);
    g_print("stop acknowledged=%d%s%s\n", ok, error ? " error=" : "", error ? error->message : "");
    if (output) qmi_message_loc_stop_output_unref(output);
    g_clear_error(&error);
    g_main_loop_quit(s->loop);
}
static gboolean finish(gpointer user_data) {
    State *s = user_data;
    if (s->stopping) return G_SOURCE_REMOVE;
    s->stopping = TRUE;
    if (s->loc && s->started) {
        QmiMessageLocStopInput *input = qmi_message_loc_stop_input_new();
        qmi_message_loc_stop_input_set_session_id(input, 42, NULL);
        qmi_client_loc_stop(s->loc, input, 5, NULL, stopped, s);
        qmi_message_loc_stop_input_unref(input);
    } else g_main_loop_quit(s->loop);
    return G_SOURCE_REMOVE;
}
static void started(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    QmiMessageLocStartOutput *output = qmi_client_loc_start_finish(QMI_CLIENT_LOC(object), result, &error);
    if (!output || !qmi_message_loc_start_output_get_result(output, &error)) {
        if (output) qmi_message_loc_start_output_unref(output);
        failed(s, "start", error); return;
    }
    qmi_message_loc_start_output_unref(output);
    s->started = TRUE;
    g_print("start acknowledged=1 standalone=%d observe_seconds=%u\n", s->standalone, s->seconds);
    g_timeout_add_seconds(s->seconds, finish, s);
}
static void begin_session(State *s) {
    QmiMessageLocStartInput *input = qmi_message_loc_start_input_new();
    qmi_message_loc_start_input_set_session_id(input, 42, NULL);
    qmi_message_loc_start_input_set_fix_recurrence_type(input, QMI_LOC_FIX_RECURRENCE_TYPE_REQUEST_PERIODIC_FIXES, NULL);
    qmi_message_loc_start_input_set_intermediate_report_state(input, QMI_LOC_INTERMEDIATE_REPORT_STATE_ENABLE, NULL);
    qmi_message_loc_start_input_set_minimum_interval_between_position_reports(input, 1000, NULL);
    qmi_client_loc_start(s->loc, input, 10, NULL, started, s);
    qmi_message_loc_start_input_unref(input);
}
static void mode_indication(QmiClientLoc *client, QmiIndicationLocSetOperationModeOutput *output, State *s) {
    QmiLocIndicationStatus status;
    (void)client;
    if (!qmi_indication_loc_set_operation_mode_output_get_indication_status(output, &status, NULL)) return;
    s->mode_ind = TRUE;
    s->standalone = status == QMI_LOC_INDICATION_STATUS_SUCCESS;
    g_print("standalone indication_status=%u\n", status);
    if (s->mode_ack) begin_session(s);
}
static void mode_set(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    QmiMessageLocSetOperationModeOutput *output = qmi_client_loc_set_operation_mode_finish(QMI_CLIENT_LOC(object), result, &error);
    if (!output || !qmi_message_loc_set_operation_mode_output_get_result(output, &error)) {
        if (output) qmi_message_loc_set_operation_mode_output_unref(output);
        failed(s, "standalone-mode", error); return;
    }
    qmi_message_loc_set_operation_mode_output_unref(output);
    s->mode_ack = TRUE;
    if (s->mode_ind) begin_session(s);
}
static void registered(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    QmiMessageLocRegisterEventsOutput *output = qmi_client_loc_register_events_finish(QMI_CLIENT_LOC(object), result, &error);
    if (!output || !qmi_message_loc_register_events_output_get_result(output, &error)) {
        if (output) qmi_message_loc_register_events_output_unref(output);
        failed(s, "register-events", error); return;
    }
    qmi_message_loc_register_events_output_unref(output);
    g_print("events registered=1\n");
    QmiMessageLocSetOperationModeInput *input = qmi_message_loc_set_operation_mode_input_new();
    qmi_message_loc_set_operation_mode_input_set_operation_mode(input, QMI_LOC_OPERATION_MODE_STANDALONE, NULL);
    qmi_client_loc_set_operation_mode(s->loc, input, 10, NULL, mode_set, s);
    qmi_message_loc_set_operation_mode_input_unref(input);
}
static void client_ready(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    s->loc = QMI_CLIENT_LOC(qmi_device_allocate_client_finish(QMI_DEVICE(object), result, &error));
    if (!s->loc) { failed(s, "allocate-loc", error); return; }
    g_signal_connect(s->loc, "position-report", G_CALLBACK(position), s);
    g_signal_connect(s->loc, "gnss-sv-info", G_CALLBACK(satellites), s);
    g_signal_connect(s->loc, "engine-state", G_CALLBACK(engine), s);
    g_signal_connect(s->loc, "set-operation-mode", G_CALLBACK(mode_indication), s);
    QmiMessageLocRegisterEventsInput *input = qmi_message_loc_register_events_input_new();
    qmi_message_loc_register_events_input_set_event_registration_mask(input,
        QMI_LOC_EVENT_REGISTRATION_FLAG_POSITION_REPORT | QMI_LOC_EVENT_REGISTRATION_FLAG_GNSS_SATELLITE_INFO |
        QMI_LOC_EVENT_REGISTRATION_FLAG_ENGINE_STATE | QMI_LOC_EVENT_REGISTRATION_FLAG_FIX_SESSION_STATE, NULL);
    qmi_client_loc_register_events(s->loc, input, 10, NULL, registered, s);
    qmi_message_loc_register_events_input_unref(input);
}
static void opened(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    if (!qmi_device_open_finish(QMI_DEVICE(object), result, &error)) { failed(s, "open", error); return; }
    qmi_device_allocate_client(s->device, QMI_SERVICE_LOC, QMI_CID_NONE, 10, NULL, client_ready, s);
}
static void device_ready(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    (void)object;
    s->device = qmi_device_new_from_node_finish(result, &error);
    if (!s->device) { failed(s, "device", error); return; }
    qmi_device_open(s->device, QMI_DEVICE_OPEN_FLAGS_NONE, 10, NULL, opened, s);
}
static void bus_ready(GObject *object, GAsyncResult *result, gpointer user_data) {
    State *s = user_data;
    GError *error = NULL;
    (void)object;
    s->bus = qrtr_bus_new_finish(result, &error);
    if (!s->bus) { failed(s, "qrtr-bus", error); return; }
    QrtrNode *node = qrtr_bus_peek_node(s->bus, 3);
    if (!node) { failed(s, "qrtr-node-3", NULL); return; }
    qmi_device_new_from_node(node, NULL, device_ready, s);
}
int main(int argc, char **argv) {
    State s = { .seconds = argc > 1 ? (guint)atoi(argv[1]) : 90 };
    if (s.seconds < 5 || s.seconds > 300) return 2;
    setvbuf(stdout, NULL, _IOLBF, 0);
    s.loop = g_main_loop_new(NULL, FALSE);
    g_unix_signal_add(SIGTERM, finish, &s);
    g_unix_signal_add(SIGINT, finish, &s);
    g_timeout_add_seconds(s.seconds + 40, finish, &s);
    qrtr_bus_new(1000, NULL, bus_ready, &s);
    g_main_loop_run(s.loop);
    g_print("summary started=%d standalone=%d satellite_reports=%u max_satellites=%u position_reports=%u coordinate_reports=%u valid_fixes=%u\n",
            s.started, s.standalone, s.sv_reports, s.max_satellites, s.position_reports, s.coordinate_reports, s.fixes);
    return s.fixes ? 0 : s.started ? 3 : 1;
}
