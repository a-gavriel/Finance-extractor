# Import Required Library
from tkinter import *
from datetime import datetime, timedelta
from tkcalendar import Calendar

selecting_start_day = True
first_selection = True
DATETIME_FORMATER= "%Y/%m/%d"

def select_date(value_as_list : list, as_lib = True) -> None:

    root = Tk()
    today = datetime.today()
    end_date = today + timedelta(days=1)
    end_date_str = end_date.strftime(DATETIME_FORMATER)
    root.geometry("250x270")

    value_as_list.clear()
    value_as_list.extend(["",end_date_str])

    cal = Calendar(root, selectmode = 'day',
                year = today.year, month = today.month,
                day = today.day, date_pattern="yyyy/mm/dd")

    cal.place(x=0, y=0)


    def on_date_select(_event):
        """Callback function executed when a date is selected in the Calendar."""
        global selecting_start_day, first_selection
        SELECTED_TAG = "selected"
        # Clear all events
        cal.calevent_remove(tag=SELECTED_TAG)

        selected_date = cal.get_date()
        if selecting_start_day:
            value_as_list[0] = selected_date
            date_range_start_label.config(text = "Start: "+selected_date)
        else:
            value_as_list[1] = selected_date
            date_range_end_label.config(text = "End: " + selected_date)

        if selecting_start_day:
            start_date = datetime.strptime(value_as_list[0], DATETIME_FORMATER)
            cal.calevent_create(start_date, "selected Day", tags=SELECTED_TAG)

        if first_selection or not selecting_start_day:
            start_date = datetime.strptime(value_as_list[0], DATETIME_FORMATER)
            current_date = start_date
            end_date = datetime.strptime(value_as_list[1], DATETIME_FORMATER)
            delta = timedelta(days=1)
            while current_date <= end_date:
                cal.calevent_create(current_date, "selected Day", tags=SELECTED_TAG)
                current_date += delta

        first_selection = False
        selecting_start_day = not selecting_start_day


    def end_selection():
        if as_lib:
            root.destroy()

    # Add Button and Label
    btn1=Button(root, text = "Select date range",
        command = end_selection)
    btn1.place(x=125,y=230, anchor=CENTER)

    date_range_start_label = Label(root, text = "Start: ")
    date_range_start_label.place(x=15, y = 190)
    date_range_end_label = Label(root, text = "End: "+ end_date_str)
    date_range_end_label.place(x=125, y = 190)

    cal.bind("<<CalendarSelected>>", on_date_select)

    # Execute Tkinter
    root.mainloop()

if __name__ == "__main__":
    print("Testing select_calendar.py lib")
    selected_values = []
    select_date(selected_values, as_lib=False)
    print(selected_values)