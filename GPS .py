import io
import sys, os
import threading
import json
import glob
import math
from time import time
from datetime import datetime

# -- Tkinter lib
if sys.version_info[0] < 3:
    import Tkinter as tk
    import ttk, tkMessageBox as msgBox, tkFileDialog as dialog
else:
    import tkinter as tk
    from tkinter import ttk, messagebox as msgBox, filedialog as dialog

# -- Matplot lib
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style

# KALMAN FILTER
#from kalman import kalman_filter

style.use("ggplot")
# -- end

# -- GPS
from gps import *

# -- Global vars config
import conf

final_file_count = 1
choosen_file = None

# -------------------------------------------------------------
#                       PLOT GRAPH
# -------------------------------------------------------------

fig_a = Figure(figsize=(7.2, 3.8), dpi=100)
plot_a = fig_a.add_subplot(111)
fig_a.subplots_adjust(left=0.12, right=0.94, top=0.94)

def animate_a(i):
    # cek file exists, dan buat file
    if not os.path.exists(conf.TRACK_TMP_FILE) and not os.path.exists(conf.TRACKBACK_TMP_FILE):
        # buat track data file
        trackData = open(conf.TRACK_TMP_FILE, "w")
        trackData.write()
        trackData.close()
        # buat trackback data file
        trackbackData = open(conf.TRACKBACK_TMP_FILE, "w")
        trackbackData.write()
        trackbackData.close()

    trackData = open(conf.TRACK_TMP_FILE, "r").read()
    trackbackData = open(conf.TRACKBACK_TMP_FILE, "r").read()

    trackList = trackData.split('\n')
    trackbackList = trackbackData.split('\n')

    tr_xList = []
    tr_yList = []

    for eachLine in trackList:
        if len(eachLine) > 1:
            lat, long = eachLine.split(',')
            tr_xList.append(float(long))
            tr_yList.append(float(lat))

    tb_xList = []
    tb_yList = []
    
    for eachLine in trackbackList:
        if len(eachLine) > 1:
            lat, long = eachLine.split(',')
            tb_xList.append(float(long))
            tb_yList.append(float(lat))

    plot_a.clear()

    tracking_line, = plot_a.plot(tr_xList, tr_yList, conf.BLUE, lw=2)
    trackback_line, = plot_a.plot(tb_xList, tb_yList, conf.ORANGE, lw=2)

    tracking_line.set_data(tr_xList, tr_yList)
    trackback_line.set_data(tb_xList, tb_yList)

    plot_a.set_ylabel('Latitude', fontsize=10)
    plot_a.set_xlabel('Longitude', fontsize=10)

    plot_a.tick_params(labelsize='x-small', width=3)


# -------------------------------------------------------------
#                      MAIN APP PAGES
# -------------------------------------------------------------

class App(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.geometry('%dx%d+0+0' % (conf.WIDTH, conf.HEIGHT))

        tk.Tk.wm_title(self, "GPS TrackBack")

        container = tk.Frame(self, bg="white")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, GraphPage, OpenPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()
        if frame.canvas:
            frame.canvas.draw_idle()



# -------------------------------------------------------------
#                      START APP
# -------------------------------------------------------------

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.canvas = False
        # Labels
        label = tk.Label(self, text="GPS TrackBack", font=conf.LARGE_FONT)
        label.place(relx=.5, rely=.38, anchor="c")

        # New Buttons
        new_button = tk.Button(self, text="New", height=2, width=12, pady=2, relief=tk.SOLID, bd=1,
                             command=lambda: controller.show_frame(GraphPage))
        new_button.place(relx=.325, rely=.58, anchor="c")
        
        # Open Buttons
        open_button = tk.Button(self, text="Open", height=2, width=12, pady=2, relief=tk.SOLID, bd=1,
                                command=lambda: controller.show_frame(OpenPage))
        open_button.place(relx=.5, rely=.58, anchor="c")
        
        # Exit Buttons
        exit_button = tk.Button(self, text="Exit", height=2, width=12, pady=2, relief=tk.SOLID, bd=1,
                             command=sys.exit)
        exit_button.place(relx=.675, rely=.58, anchor="c")



# -------------------------------------------------------------
#                      GRAPH APP PAGES
# -------------------------------------------------------------

class GraphPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        buttonframe = tk.Frame(self)
        buttonframe.pack(side=tk.RIGHT, fill=tk.Y, expand=True, pady=(2, 9), padx=6)
        # global vars
        global gps_stats, track_button, trackback_button, gps_stats, save_button, track_done, trackback_done
        
        # Track button
        track_button = tk.Button(buttonframe, text="Track", height=2, width=12, relief=tk.SOLID, bd=1,
                             command=self.track_clicked)
        track_button.pack(side=tk.TOP, pady=4)
        
        # TrackBack button
        trackback_button = tk.Button(buttonframe, text="TrackBack", height=2, width=12, relief=tk.SOLID, bd=1,
                                     state="disabled", command=self.trackback_clicked)
        trackback_button.pack(side=tk.TOP, pady=4)
        
        # Save data button
        save_button = tk.Button(buttonframe, text="Save", height=2, width=12, relief=tk.SOLID, bd=1,
                                state="active", command=self.save_clicked)
        save_button.pack(side=tk.TOP, pady=8)

        # GPS Text Stats
        gps_stats = tk.Label(buttonframe, text="Ready", font=conf.SMALL_FONT)
        gps_stats.pack(side=tk.BOTTOM, pady=(4, 0))

        # Exit Button
        exit_button = tk.Button(buttonframe, text="Exit", height=2, width=12, relief=tk.SOLID, bd=1,
                                command=sys.exit)
        exit_button.pack(side=tk.BOTTOM, pady=(4, 1))
        
        # Back to Home Button
        home_button = tk.Button(buttonframe, text="Home", height=2, width=12, relief=tk.SOLID, bd=1,
                                command=lambda: controller.show_frame(StartPage))
        home_button.pack(side=tk.BOTTOM, pady=4)

        # Canvas A
        canvas_a = FigureCanvasTkAgg(fig_a, self)
        canvas_a.draw()
        canvas_a.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.X, expand=True)

        toolbar = NavigationToolbar2TkAgg(canvas_a, self)
        toolbar.update()
        canvas_a._tkcanvas.pack(side=tk.TOP, fill=tk.Y, expand=True)

        self.canvas = canvas_a

        # Thread var
        self.tr = None
        self.tb = None
        self.sv = None

        # Track and TrackBack data
        self.track_data = None
        self.trackback_data = None

        # GPS var
        self.gpsd = None
        
        # Run state var
        self.running = False

        # Track and Trackback job vars
        track_done = False
        trackback_done = False

        # Data final nama file
        self.final_file_name = "{:%d-%m-%Y}.json".format(datetime.now())
        self.final_file = os.path.join(conf.DATA_PATH, self.final_file_name)

    # ------------------------------------
    # -- tracking_button click --
    # ------------------------------------
    def track_clicked(self):
        # global vars
        global gps_stats, track_button
        # Initiate threading process
        self.tr = threading.Thread(target=self.run_tracking)
        # Starting threading process
        self.tr.start()
        # track_button
        track_button.configure(text="Stop", bg=conf.BLUE, fg="white", command=self.stop_tracking)
        # Change gps var stats
        gps_stats.config(text="Tracking Started", fg=conf.BLUE)
    
    # --------------------------
    # -- proses tracking --
    # --------------------------
    def run_tracking(self):
        global gps_stats, track_done
        try:
            # Set runnning var to true
            self.running = True
            self.gpsd = gps(mode=WATCH_ENABLE)

            print ""
            print "Tracking Started"
            print"----------------"

            # Open tmp track_data files
            self.track_data = open(conf.TRACK_TMP_FILE, "w+")

            # inisialisasi kalman filter latitude
            Qlat = 0 #inisialisasi Q latitude
            Rlat = 1 #inisialisasi R latitude
            xhatlat = 0 #inisialisasi xhat latitude
            Plat = 0.00001 #inisialisasi P latitude
            
            # inisialisasi kalman filter longitude
            Qlong = 0 #inisialisasi Q longitude
            Rlong = 1 #inisialisasi R longitude
            xhatlong = 0 #inisialisasi xhat longitude
            Plong = 0.00001 #inisialisasi P longitude
            
            # pengambilan data koordinat dengan gpsd.next
            while self.running:
                # gpsd func
                self.gpsd.next()
                # fix latitude dan longitude
                latitude  = self.gpsd.fix.latitude
                xhatlat = self.gpsd.fix.latitude
                longitude = self.gpsd.fix.longitude
                xhatlong = self.gpsd.fix.longitude
                # Kalman filtering latitude
                xhatlatbef = xhatlat # X(k-1) latitude
                Platbef = Plat+Qlat #P(k-1) latitudr

                Klat = Platbef / (Platbef + Rlat) #K latitude
                xhatlat = xhatlatbef + Klat + (latitude-xhatlatbef) #xhat latitude update
                Plat = (1-Klat)*Platbef #P latitude baru update
                # Kalman filtering longitude
                xhatlongbef = xhatlong # X(k-1) longitude
                Plongbef = Plong+Qlong #P(k-1) longitude

                Klong = Plongbef / (Plongbef + Rlong) #K longitude
                xhatlong = xhatlongbef + Klong + (longitude-xhatlongbef) #xhat latitude update
                Plong = (1-Klong)*Plongbef #P latitude baru update
                # tulis data ke files jika lat,long kosong
                if not math.isnan(latitude) and not math.isnan(longitude) and latitude != 0.0 and longitude != 0.0:
                    # Data format
                    data = "{:.6f},{:.6f}".format(float(latitude),float(longitude))
                    datakalman = "{:.6f},{:.6f}".format(float(xhatlat),float(xhatlong)) #data kalaman
                    # buat data
                    #self.track_data.write(str(data) + '\n')
                    self.track_data.write(str(datakalman) + '\n')
                    # Flush data sehingga data dapat di lihat
                    self.track_data.flush()
                    os.fsync(self.track_data)
                    # print 
                    print(data)
                    print(datakalman)
                    # status gps on
                    gps_stats.config(text="Run Tracking", fg=conf.BLUE)
                else:
                    print "No Signal..."
                    # status gps off
                    gps_stats.config(text="No Signal", fg=conf.RED)
                # delay
                time.sleep(1)

        except (KeyboardInterrupt, SystemExit):
            if self.running:
                #berhenti tracking
                self.running = False
                
                self.tr.join()
                # Tracking selesai
                track_done = True
            print "Tracking Stopped" 

    # ---------------------------
    # -- Stop tracking --
    # ---------------------------
    def stop_tracking(self):
        # Global vars
        global track_button, trackback_button, gps_stats, track_done
        # Set running state ke false
        self.running = False
        if self.tr.isAlive():
            self.track_data.close()
            
            self.tr.join()
            # klik buttons
            track_button.configure(state="disabled", text="Stopped", bg=conf.DISABLED, fg="black") # disabled
            trackback_button.configure(state="active")  # active
            # status gps
            gps_stats.config(text="Stopped", fg=conf.BLUE)
        track_done = True
        print "Tracking Stopped"

    # ------------------------------------
    # -- trackback_button clicked --
    # ------------------------------------
    def trackback_clicked(self):
        # global vars
        global gps_stats, trackback_button
        # Initiate threading process
        self.tb = threading.Thread(target=self.run_trackback)
        # Starting threading process
        self.tb.start()
        # klik track_button
        trackback_button.configure(text="Stop", bg=conf.ORANGE, fg="white", command=self.stop_trackingback)
        gps_stats.config(text="TrackBack Started", fg=conf.ORANGE)

    # ------------------------------
    # -- trackingback proses --
    # ------------------------------
    def run_trackback(self):
        global gps_stats, trackback_done
        try:
            # Set runnning var ke true
            self.running = True

            print ""
            print "TrackingBack Started"
            print "----------------"

            # membuka tmp track_data files
            self.trackback_data = open(conf.TRACKBACK_TMP_FILE, "w+")

            # inisialisasi kalman filter latitude
            Qlat = 0 #inisialisasi Q latitude
            Rlat = 1 #inisialisasi R latitude
            xhatlat = 0 #inisialisasi xhat latitude
            Plat = 0.00001 #inisialisasi P latitude
            
            # inisialisasi kalman filter longitude
            Qlong = 0 #inisialisasi Q longitude
            Rlong = 1 #inisialisasi R longitude
            xhatlong = 0 #inisialisasi xhat longitude
            Plong = 0.00001 #inisialisasi P longitude
            
            # Get data by iterate over gpsd.next
            while self.running:
                # gpsd func
                self.gpsd.next()
                # fix latitude dan longitude
                latitude  = self.gpsd.fix.latitude
                xhatlat = self.gpsd.fix.latitude
                longitude = self.gpsd.fix.longitude
                xhatlong = self.gpsd.fix.longitude
                # Kalman filtering untuk latitude
                xhatlatbef = xhatlat # X(k-1) latitude
                Platbef = Plat+Qlat #P(k-1) latitudr

                Klat = Platbef / (Platbef + Rlat) #K latitude
                xhatlat = xhatlatbef + Klat + (latitude-xhatlatbef) #xhat latitude update
                Plat = (1-Klat)*Platbef #P latitude baru update
                # Kalman filtering untuk longitude
                xhatlongbef = xhatlong # X(k-1) longitude
                Plongbef = Plong+Qlong #P(k-1) longitude

                Klong = Plongbef / (Plongbef + Rlong) #K longitude
                xhatlong = xhatlongbef + Klong + (longitude-xhatlongbef) #xhat latitude update
                Plong = (1-Klong)*Plongbef #P latitude baru update
                # Write data format to files if lat,long not None
                if not math.isnan(latitude) and not math.isnan(longitude) and latitude != 0.0 and longitude != 0.0:
                    # Data format
                    data = "{:.6f},{:.6f}".format(float(latitude),float(longitude))
                    datakalman = "{:.6f},{:.6f}".format(float(xhatlat),float(xhatlong)) 
                    # Write data
                    #self.trackback_data.write(str(data) + '\n')
                    self.trackback_data.write(str(datakalman) + '\n')
                    # Flush data 
                    self.trackback_data.flush()
                    os.fsync(self.trackback_data)
                    # print 
                    print (data)
                    print (datakalman) 
                    # gps var status
                    gps_stats.config(text="Run TrackBack", fg=conf.ORANGE)
                else:
                    print "No Signal..."
                    # gps var status
                    gps_stats.config(text="No Signal", fg=conf.RED)
                # delay
                time.sleep(1)

        except (KeyboardInterrupt, SystemExit):
            if self.running:
                # ubah running state ke false
                self.running = False
                self.tb.join()
                # tracking selesai
                trackback_done = True
            print "Tracking Stopped" 

    # -------------------------------
    # -- Stop trackingback prosess --
    # -------------------------------
    def stop_trackingback(self):
        # Global vars
        global trackback_button, gps_stats, save_button, trackback_done
        # Set running state ke false
        self.running = False
        if self.tb.isAlive():
            # Close trackback data
            self.trackback_data.close()
            self.tb.join()
            # click button
            trackback_button.configure(state="disabled", text="Stopped", bg=conf.DISABLED, fg="black") # active
            # gps status
            gps_stats.config(text="Stopped", fg=conf.ORANGE)
        # tracking selesai
        trackback_done = True
        
        if track_done and trackback_done:
            # Click save untuk menyimpan
            save_button.configure(state="active", bg=conf.GREEN, fg=conf.WHITE)
        print "TrackingBack Stopped"

    # ------------------------------------
    # -- save_button clicked --
    # ------------------------------------
    def save_clicked(self):
        # global vars
        global gps_stats, save_button
        # threading proses
        self.sv = threading.Thread(target=self.saving_data)
        # Start threading process
        self.sv.start()
        # Click save_button
        save_button.configure(text="Saving Data...", state="disabled", fg=conf.WHITE)
        # gps var status
        gps_stats.config(text="Saving gps data...", fg=conf.GREEN)

    # ------------------------------
    # -- saving data process --
    # ------------------------------
    def saving_data(self):
        global gps_stats, final_file_count, save_button

        while os.path.exists(self.final_file):
            self.final_file_name = "{:%d-%m-%Y}_{}.json".format(datetime.now(), final_file_count)
            self.final_file = os.path.join(conf.DATA_PATH, self.final_file_name)
            final_file_count += 1

        final_data = {}

        for fname in [conf.TRACK_TMP_FILE, conf.TRACKBACK_TMP_FILE]:
            print("Adding", fname)

            in_file = os.path.join(conf.TMP_PATH, fname)
            if os.path.isfile(in_file):
                with open(fname, 'r') as file_in:
                    content = file_in.read()
                    content = content.split('\n')

                    content_lat = []
                    content_long = []
                    get_filename = os.path.splitext(os.path.basename(in_file))[0]

                    for eachLine in content:
                        if len(eachLine) > 1:
                            lat, long = eachLine.split(',')
                            content_lat.append(str(lat))
                            content_long.append(str(long))

                    final_data.update({
                        get_filename: [
                            {
                                'latitude': content_lat,
                                'longitude': content_long,
                            }
                        ]
                    })
                self.append_record(self.final_file, final_data)
            else:
                print "Error saving data"
                msgBox.showerror("Error", "An error occured while saving data.")


        if os.path.isfile(self.final_file):
            print "File saved successfully"
            # Click save_button
            save_button.configure(text="Saved", state="disabled")
            msg = "Data has been saved successfully as \n" + self.final_file_name
            # gps var status
            gps_stats.config(text="File Saved", fg=conf.GREEN)
            
            msgBox.showerror("Data Saved", msg)

    def append_record(self, filename, record):
        with open(filename, 'w+') as json_file:
            data = json.dumps(record, ensure_ascii=False)
            json_file.write(str(data))


# -------------------------------------------------------------
#                      MAIN APP PAGES
# -------------------------------------------------------------

class OpenPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        buttonframe = tk.Frame(self)
        buttonframe.pack(side=tk.RIGHT, fill=tk.Y,
                         expand=False, pady=(2, 9), padx=6)

        # Open button
        open_button = tk.Button(buttonframe, text="Open", height=2, width=12, relief=tk.SOLID, bd=1,
                                command=self.get_file)
        open_button.pack(side=tk.TOP, pady=4)

        # Exit Button
        exit_button = tk.Button(buttonframe, text="Exit", height=2, width=12, relief=tk.SOLID, bd=1,
                                command=sys.exit)
        exit_button.pack(side=tk.BOTTOM, pady=(4, 1))

        # Back to Home Button
        home_button = tk.Button(buttonframe, text="Home", height=2, width=12, relief=tk.SOLID, bd=1,
                                command=lambda: controller.show_frame(StartPage))
        home_button.pack(side=tk.BOTTOM, pady=4)


        # ------
        self.fig_b = Figure(figsize=(7.2, 3.8), dpi=100)
        self.plot_b = self.fig_b.add_subplot(111)
        self.fig_b.subplots_adjust(left=0.12, right=0.94, top=0.94)

        # Open default lates files
        list_of_files = glob.glob(conf.DATA_PATH + '*.json')
        latest_file = max(list_of_files, key=os.path.getctime)
        # Default file to open var
        self.file_to_open = os.path.join(conf.DATA_PATH, "s.json")

        self.plot_b.clear()

        self.tracking_line, = self.plot_b.plot([], [], '.-', color=conf.BLUE, lw=2)
        self.trackback_line, = self.plot_b.plot([], [], '.-', color=conf.ORANGE, lw=2)

        self.plot_b.set_ylabel('Latitude', fontsize=10)
        self.plot_b.set_xlabel('Longitude', fontsize=10)

        self.plot_b.tick_params(labelsize='x-small', width=3)

        # Canvas A
        self.canvas_b = FigureCanvasTkAgg(self.fig_b, self)
        self.canvas_b.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.toolbar = NavigationToolbar2TkAgg(self.canvas_b, self)
        self.toolbar.update()
        self.canvas_b._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = self.canvas_b


    def get_file(self):
        name = dialog.askopenfilename(initialdir=conf.DATA_PATH,
                                        filetypes=(("JSON Files", "*.json"),),
                                        title="Choose a file.")
        choosen_file = name
        print("Opening file {}".format(name))
        # OpenFile() frames
        return self.open_file(choosen_file)

    
    def open_file(self, filename):
        # try:
        tr_latList = []
        tr_longList = []
        
        tb_latList = []
        tb_longList = []

        with open(filename) as f:
            dt = json.load(f)
            for tr in dt['track']:
                for lat in tr['latitude']:
                    tr_latList.append(float(lat))
                for long in tr['longitude']:
                    tr_longList.append(float(long))
            for tb in dt['trackback']:
                for lat in tb['latitude']:
                    tb_latList.append(float(lat))
                for long in tb['longitude']:
                    tb_longList.append(float(long))

        self.tracking_line.set_data(tr_longList, tr_latList)
        self.trackback_line.set_data(tb_longList, tb_latList)
        print("Redrawing canvas...")
        ax = self.canvas_b.figure.axes[0]
        ax.set_xlim(min(min(tr_longList), min(tb_longList)), max(max(tr_longList), max(tb_longList)))
        ax.set_ylim(min(min(tr_latList), min(tb_latList)), max(max(tr_latList), max(tb_latList)))
        self.canvas_b.draw()

if __name__ == "__main__":
    app = App()
    aniA = animation.FuncAnimation(fig_a, animate_a, interval=1000, blit=False)
    app.mainloop()
