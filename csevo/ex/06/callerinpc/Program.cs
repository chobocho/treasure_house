// 슬라이드 p6-v5-caller-inpc — INotifyPropertyChanged, C# 5.0
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;

class Person : INotifyPropertyChanged
{
    public event PropertyChangedEventHandler PropertyChanged;
    // One helper for every setter: no property name in the source.
    bool Set<T>(ref T field, T value,
        [CallerMemberName] string name = null)
    {
        if (EqualityComparer<T>.Default.Equals(field, value))
            return false;
        field = value;
        PropertyChangedEventHandler h = PropertyChanged;
        if (h != null) h(this, new PropertyChangedEventArgs(name));
        return true;
    }

    string first;
    public string First
    { get { return first; } set { Set(ref first, value); } }
    int age;
    public int Age { get { return age; } set { Set(ref age, value); } }
}

class App
{
    static void Main()
    {
        Person p = new Person();
        p.PropertyChanged += (s, e) =>
            Console.WriteLine("changed: " + e.PropertyName);
        p.First = "Ada";
        p.Age = 36;
        p.Age = 36;
    }
}
