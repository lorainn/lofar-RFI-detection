import imageio
import os
import numpy as np
import matplotlib.pyplot as plt

from lofarimaging import sky_imager, make_sky_plot

def make_sky_video(visibilities_all, baselines, freq, marked_all_lmn, marked_sats_traj_lmn, station_name, subband, obstime, 
                   fname, t_end, t_start=0, step=1, npix=131, fps=5, output_dir='./videoresult'):

    os.makedirs(output_dir, exist_ok=True)
   
    # static background
    #n_med = min(n_for_median, visibilities_all.shape[0])
    #vis_median = np.median(visibilities_all[:n_med], axis=0)
    #print(f"Median background")

    timesteps = range(t_start, t_end, step)

    frames = []
    for i, t_idx in enumerate(timesteps):
        #vis_residual = visibilities_all[t_idx] - vis_median
        img_t = sky_imager(visibilities_all[t_idx], baselines, freq, npix, npix)
        frames.append(img_t)
        print(f"  Frame {i+1}/{len(timesteps)}", end='\r')
    print(f"\nAll frames done")

    # render and save GIF
    gif_path = os.path.join(output_dir, f'{fname}_skyvideo_fps{fps}.gif')
    gif_frames = []

    for i, img_t in enumerate(frames):
        t_idx = t_start + i * step
        fig = make_sky_plot(img_t, marked_all_lmn, title=f"Sky image {station_name}", 
                            subtitle=f"SB {subband} ({freq/1e6:.1f} MHz) — t={t_idx}")
        
        for sat_name, (l, m, n) in marked_sats_traj_lmn.items():
            fig.axes[0].plot(l, m, color='white', linestyle='-', alpha=0.3, linewidth=0.8)

        fig.canvas.draw()
        frame_img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        frame_img = frame_img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
        gif_frames.append(frame_img)
        plt.close(fig)

    imageio.mimsave(gif_path, gif_frames, fps=fps)
    print(f"GIF saved: {gif_path}")
    return gif_path