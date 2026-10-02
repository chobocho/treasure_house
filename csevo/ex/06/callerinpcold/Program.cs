// 슬라이드 p6-v5-caller-inpcold — 이전엔 이름을 문자열로, C# 4.0
using System;
using System.ComponentModel;

class Person : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler PropertyChanged;

    void OnPropertyChanged(string name)
    {
        PropertyChangedEventHandler h = PropertyChanged;
        if (h != null) h(this, new PropertyChangedEventArgs(name));
    }

    // Renamed from "Name" to "FullName"; the string was not.
    string fullName;
    public string FullName
    {
        get { return fullName; }
        set { fullName = value; OnPropertyChanged("Name"); }
    }
}

class App
{
    static void Main()
    {
        Person p = new Person();
        p.PropertyChanged += (s, e) =>
        {
            bool ok =
                typeof(Person).GetProperty(e.PropertyName) != null;
            Console.WriteLine("changed: " + e.PropertyName
                + (ok ? "" : "  <- no such member"));
        };
        p.FullName = "Ada Lovelace";
    }
}
