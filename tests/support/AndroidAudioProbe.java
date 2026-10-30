package org.omarchy.apollo;

import java.lang.reflect.Method;
import java.io.FileWriter;

/** Synthetic AudioTrack transport probe; run only against the isolated sink. */
public final class AndroidAudioProbe {
    public static void main(String[] args) throws Exception {
        try {
            runProbe();
            System.exit(0);
        } catch (Throwable failure) {
            failure.printStackTrace();
            report("{\"failed\":true,\"error_type\":\"" + failure.getClass().getName() + "\"}");
            System.exit(2);
        }
    }

    private static void report(String result) throws Exception {
        try (FileWriter writer = new FileWriter("/data/local/tmp/omarchy-apollo-audio-result.json")) {
            writer.write(result);
        }
        System.out.println(result);
    }

    private static void runProbe() throws Exception {
        report("{\"stage\":\"starting\"}");
        final int rate = 48000;
        final int frames = rate * 3;
        // Reflection keeps compilation independent of SDK stubs. At runtime the
        // actual Android boot framework supplies AudioTrack and its native HAL.
        Class<?> api = Class.forName("android.media.AudioTrack");
        if (api.getClassLoader() == AndroidAudioProbe.class.getClassLoader()) {
            throw new IllegalStateException("AudioTrack must come from the boot framework");
        }
        int minimum = (Integer) api.getMethod("getMinBufferSize", int.class,
                int.class, int.class).invoke(null, rate, 12, 2);
        if (minimum <= 0) throw new IllegalStateException("No stereo PCM16 output");
        report("{\"stage\":\"constructing\"}");
        Object track = api.getConstructor(int.class, int.class, int.class,
                int.class, int.class, int.class).newInstance(3, rate, 12, 2,
                Math.max(minimum * 4, 19200), 1);
        Method release = api.getMethod("release");
        try {
            int state = (Integer) api.getMethod("getState").invoke(track);
            if (state != 1) throw new IllegalStateException("AudioTrack not initialized");
            report("{\"stage\":\"initialized\"}");
            api.getMethod("setVolume", float.class).invoke(track, 0.5f);
            short[] samples = new short[frames * 2];
            for (int frame = 0; frame < frames; frame++) {
                double envelope = Math.min(1.0, Math.min(frame, frames - 1 - frame) / 480.0);
                samples[2 * frame] = (short) (8000 * envelope * Math.sin(2 * Math.PI * 997 * frame / rate));
                samples[2 * frame + 1] = (short) (8000 * envelope * Math.sin(2 * Math.PI * 1499 * frame / rate));
            }
            Method write = api.getMethod("write", short[].class, int.class, int.class, int.class);
            Method position = api.getMethod("getPlaybackHeadPosition");
            api.getMethod("play").invoke(track);
            report("{\"stage\":\"playing\"}");
            int offset = 0;
            long writeDeadline = System.nanoTime() + 10000000000L;
            while (offset < samples.length) {
                int count = (Integer) write.invoke(track, samples, offset,
                        Math.min(9600, samples.length - offset), 1);
                if (count < 0) throw new IllegalStateException("AudioTrack write failed");
                offset += count;
                if (System.nanoTime() >= writeDeadline) throw new IllegalStateException("AudioTrack write stalled");
                if (count == 0) Thread.sleep(5);
            }
            report("{\"stage\":\"written\"}");
            long deadline = System.nanoTime() + 5000000000L;
            int played;
            do {
                played = (Integer) position.invoke(track);
                if (played >= frames) break;
                if (System.nanoTime() >= deadline) throw new IllegalStateException("Playback stalled");
                Thread.sleep(20);
            } while (true);
            api.getMethod("stop").invoke(track);
            report("{\"framework_audio_track\":true,\"sample_rate\":" + rate
                    + ",\"channels\":2,\"frames_written\":" + frames
                    + ",\"frames_played\":" + played + "}");
        } finally {
            release.invoke(track);
        }
    }
}
