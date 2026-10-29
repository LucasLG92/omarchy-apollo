/* SPDX-License-Identifier: GPL-2.0-only */
/* Wait for an announced service, without starting or configuring GNSS. */
#include <libqrtr-glib.h>
#include <stdio.h>

typedef struct {
    GMainLoop *loop;
    QrtrBus *bus;
    gboolean ready;
} State;

static gboolean check(gpointer data)
{
    State *s = data;
    QrtrNode *node;
    gint32 port;
    if (!s->bus) return G_SOURCE_CONTINUE;
    node = qrtr_bus_peek_node(s->bus, 3);
    if (!node) return G_SOURCE_CONTINUE;
    port = qrtr_node_lookup_port(node, 16); /* SDX55 LOC */
    if (port < 0) return G_SOURCE_CONTINUE;
    s->ready = TRUE;
    printf("SDX55 LOC is announced on QRTR node 3, port %d\n", port);
    g_main_loop_quit(s->loop);
    return G_SOURCE_REMOVE;
}

static gboolean expired(gpointer data)
{
    State *s = data;
    fprintf(stderr, "SDX55 LOC was not announced within 30 seconds\n");
    g_main_loop_quit(s->loop);
    return G_SOURCE_REMOVE;
}

static void bus_ready(GObject *object, GAsyncResult *result, gpointer data)
{
    State *s = data;
    GError *error = NULL;
    (void)object;
    s->bus = qrtr_bus_new_finish(result, &error);
    if (!s->bus) {
        fprintf(stderr, "QRTR discovery failed: %s\n", error->message);
        g_clear_error(&error);
        g_main_loop_quit(s->loop);
        return;
    }
    check(s);
}

int main(void)
{
    State s = {0};
    s.loop = g_main_loop_new(NULL, FALSE);
    g_timeout_add(100, check, &s);
    g_timeout_add_seconds(30, expired, &s);
    qrtr_bus_new(1000, NULL, bus_ready, &s);
    g_main_loop_run(s.loop);
    g_clear_object(&s.bus);
    g_main_loop_unref(s.loop);
    return s.ready ? 0 : 1;
}
