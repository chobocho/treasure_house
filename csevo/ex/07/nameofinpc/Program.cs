// 슬라이드 p7-v6-nameof-inpc — INotifyPropertyChanged, C# 6.0
using System;
using System.ComponentModel;

class Person : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler PropertyChanged;
    string name;
    int age;

    public string Name
    {
        get { return name; }
        set { name = value; Raise(nameof(Name)); }
    }

    public int Age
    {
        get { return age; }
        set { age = value; Raise(nameof(Age)); Raise(nameof(IsAdult)); }
    }

    public bool IsAdult { get { return age >= 18; } }

    void Raise(string property)
    {
        PropertyChanged?.Invoke(this,
            new PropertyChangedEventArgs(property));
    }
}

class App
{
    static void Main()
    {
        var p = new Person();
        p.PropertyChanged += (s, e) =>
            Console.WriteLine("changed: " + e.PropertyName);
        p.Name = "Ada";
        p.Age = 36;
    }
}
