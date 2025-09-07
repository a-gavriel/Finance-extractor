# Import Required Library
from tkinter import *
from tkcalendar import Calendar
from datetime import datetime


def select_date(value_as_list : list) -> None:
    root = Tk()
    today = datetime.today()
    
    cal = Calendar(root, selectmode = 'day',
                year = today.year, month = today.month,
                day = today.day, date_pattern="yyyy/mm/dd")

    cal.pack()

    def grad_date():
        date.config(text = "Selected Date is: " + cal.get_date())
        value_as_list.clear()
        value_as_list.append(cal.get_date())
        root.destroy()
        return

    # Add Button and Label
    Button(root, text = "Select starting date",
        command = grad_date).pack()

    date = Label(root, text = "")
    date.pack()

    # Execute Tkinter
    root.mainloop()
