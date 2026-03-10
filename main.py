import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter
import sys
import os

if sys.platform == "darwin":
    os.environ["TK_SILENCE_DEPRECATION_WARNING"] = "1"


def main():
    root = tk.Tk()
    root.title("图像二值化工具")
    root.geometry("1000x700")

    img_data = {"original": None, "display": None, "tk": None}
    roi = []
    drawing = [False]
    thresh = [127]
    binary = [None]

    morph_enable = tk.BooleanVar(value=False)
    erosion = tk.IntVar(value=1)
    dilation = tk.IntVar(value=1)

    menu = tk.Menu(root)
    file_menu = tk.Menu(menu, tearoff=0)
    menu.add_cascade(label="文件", menu=file_menu)
    root.config(menu=menu)

    main_frm = tk.Frame(root)
    main_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    left_frm = tk.Frame(main_frm, width=600)
    left_frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(left_frm, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)

    right_frm = tk.Frame(main_frm, width=300)
    right_frm.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10)

    thresh_frm = tk.Frame(right_frm)
    thresh_frm.pack(fill=tk.X, padx=10, pady=10)
    tk.Label(thresh_frm, text="二值化阈值").pack(side=tk.LEFT)
    thresh_var = tk.IntVar(value=127)
    thresh_scale = tk.Scale(thresh_frm, from_=0, to=255, orient=tk.HORIZONTAL, variable=thresh_var)
    thresh_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    morph_frm = tk.LabelFrame(right_frm, text="形态学处理")
    morph_frm.pack(fill=tk.X, padx=10, pady=10)
    morph_chk = tk.Checkbutton(morph_frm, text="启用腐蚀/膨胀", variable=morph_enable)
    morph_chk.pack(anchor=tk.W, padx=5, pady=5)
    tk.Label(morph_frm, text="腐蚀次数").pack(anchor=tk.W, padx=5)
    eros_scale = tk.Scale(morph_frm, from_=0, to=10, orient=tk.HORIZONTAL, variable=erosion)
    eros_scale.pack(fill=tk.X, padx=5)
    tk.Label(morph_frm, text="膨胀次数").pack(anchor=tk.W, padx=5)
    dila_scale = tk.Scale(morph_frm, from_=0, to=10, orient=tk.HORIZONTAL, variable=dilation)
    dila_scale.pack(fill=tk.X, padx=5)

    btn_frm = tk.Frame(right_frm)
    btn_frm.pack(fill=tk.X, padx=10, pady=10)
    
    def update_canvas():
        if not img_data["display"]:
            return
        cw = canvas.winfo_width() or 600
        ch = canvas.winfo_height() or 600
        iw, ih = img_data["display"].size
        scale = min(cw / iw, ch / ih)
        new_size = (int(iw * scale), int(ih * scale))
        resized = img_data["display"].resize(new_size, Image.LANCZOS)
        img_data["tk"] = ImageTk.PhotoImage(resized)
        canvas.delete("all")
        canvas.create_image(0, 0, anchor=tk.NW, image=img_data["tk"])
        if len(roi) == 4:
            canvas.create_rectangle(roi[0], roi[1], roi[2], roi[3], outline="red", width=2)

    def on_down(event):
        if img_data["tk"]:
            drawing[0] = True
            roi.clear()
            roi.extend([event.x, event.y, event.x, event.y])

    def on_drag(event):
        if drawing[0] and img_data["tk"] and len(roi) >= 4:
            roi[2] = event.x
            roi[3] = event.y
            update_canvas()

    def on_up(event):
        if drawing[0] and img_data["tk"] and len(roi) >= 4:
            drawing[0] = False
            roi[2] = event.x
            roi[3] = event.y
            roi[0], roi[2] = min(roi[0], roi[2]), max(roi[0], roi[2])
            roi[1], roi[3] = min(roi[1], roi[3]), max(roi[1], roi[3])
            update_canvas()

    def reset_sel():
        roi.clear()
        update_canvas()
        result_canvas.delete("all")
        binary[0] = None
        info_lbl.config(text="请框选要二值化的区域")

    def update_thresh(val):
        thresh[0] = int(val)

    def toggle_morph():
        state = tk.NORMAL if morph_enable.get() else tk.DISABLED
        eros_scale.config(state=state)
        dila_scale.config(state=state)

    def apply_morph(bimg):
        result = bimg
        for _ in range(erosion.get()):
            result = result.filter(ImageFilter.MinFilter(size=3))
        for _ in range(dilation.get()):
            result = result.filter(ImageFilter.MaxFilter(size=3))
        return result

    def show_result(img):
        cw, ch = 280, 200
        iw, ih = img.size
        scale = min(cw / iw, ch / ih)
        new_size = (int(iw * scale), int(ih * scale))
        resized = img.resize(new_size, Image.NEAREST)
        tk_img = ImageTk.PhotoImage(resized)
        result_canvas.delete("all")
        result_canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        result_canvas.image = tk_img

    def binarize_sel():
        if not img_data["original"] or len(roi) != 4:
            messagebox.showinfo("提示", "请先选择图片并框选区域")
            return
        cw = canvas.winfo_width() or 600
        ch = canvas.winfo_height() or 600
        iw, ih = img_data["original"].size
        scale = min(cw / iw, ch / ih)
        x1, y1, x2, y2 = [int(c / scale) for c in roi]
        x1 = max(0, min(x1, iw - 1))
        x2 = max(0, min(x2, iw - 1))
        y1 = max(0, min(y1, ih - 1))
        y2 = max(0, min(y2, ih - 1))
        if x1 >= x2 or y1 >= y2:
            messagebox.showinfo("提示", "所选区域无效")
            return
        roi_img = img_data["original"].crop((x1, y1, x2, y2))
        gray = roi_img.convert("L")
        bin_img = gray.point(lambda p: 255 if p > thresh[0] else 0)
        if morph_enable.get():
            bin_img = apply_morph(bin_img)
        binary[0] = bin_img
        show_result(bin_img)
        if morph_enable.get():
            info_lbl.config(text=f"处理完成: 阈值={thresh[0]}, 腐蚀={erosion.get()}, 膨胀={dilation.get()}")
        else:
            info_lbl.config(text=f"处理完成: 阈值={thresh[0]}")

    def save_file():
        if binary[0] is None:
            messagebox.showinfo("提示", "请先处理一个区域")
            return
        try:
            path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("BMP", "*.bmp")])
            if not path:
                return
            binary[0].save(path)
            messagebox.showinfo("成功", f"图像已保存到: {path}")
            info_lbl.config(text=f"已保存图像: {path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法保存图像: {e}")

    def open_file():
        print("Open file clicked")
        def do_open():
            root.update_idletasks()
            path = filedialog.askopenfilename()
            print(f"Selected: {path}")
            if path:
                img_data["original"] = Image.open(path)
                img_data["display"] = img_data["original"].copy()
                update_canvas()
                roi.clear()
                result_canvas.delete("all")
                binary[0] = None
                info_lbl.config(text=f"已加载图片: {path}")
        root.after(100, do_open)

    binarize_btn = tk.Button(btn_frm, text="二值化所选区域")
    binarize_btn.pack(fill=tk.X)
    save_btn = tk.Button(btn_frm, text="导出二值化图像")
    save_btn.pack(fill=tk.X, pady=5)
    reset_btn = tk.Button(btn_frm, text="重置选择")
    reset_btn.pack(fill=tk.X, pady=5)

    info_lbl = tk.Label(right_frm, text="请先打开图片并框选需要处理的区域", wraplength=280)
    info_lbl.pack(fill=tk.X, padx=10, pady=10)

    result_frm = tk.Frame(right_frm)
    result_frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    tk.Label(result_frm, text="结果预览:").pack(anchor=tk.W)
    result_canvas = tk.Canvas(result_frm, bg="white", width=280, height=200)
    result_canvas.pack(fill=tk.BOTH, expand=True)

    file_menu.add_command(label="打开", command=open_file)
    file_menu.add_command(label="保存二值化图像", command=save_file)
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=root.quit)

    canvas.bind("<Button-1>", on_down)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_up)

    thresh_scale.config(command=update_thresh)
    morph_chk.config(command=toggle_morph)
    binarize_btn.config(command=binarize_sel)
    save_btn.config(command=save_file)
    reset_btn.config(command=reset_sel)

    def on_config(e):
        if img_data["display"]:
            update_canvas()

    root.bind("<Configure>", on_config)
    toggle_morph()
    root.mainloop()


if __name__ == "__main__":
    main()
