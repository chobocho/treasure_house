// 슬라이드 p15-v14-fk-init — 초기화자는 setter 를 부르지 않는다, C# 14
using System;
using System.Collections.Generic;

class ViewModel
{
    public bool HasPendingChanges { get; private set; }

    public bool IsActive { get; set => Set(ref field, value); } = true;

    public string Name { get; set => Set(ref field, value); }

    public ViewModel(string name) { Name = name; }  // calls the setter

    bool Set<T>(ref T location, T value)
    {
        if (EqualityComparer<T>.Default.Equals(location, value))
            return false;
        location = value;
        HasPendingChanges = true;
        return true;
    }
}

class Program
{
    static void Main()
    {
        var a = new ViewModel(null);
        Console.WriteLine(a.IsActive + " " + a.HasPendingChanges);
        var b = new ViewModel("x");
        Console.WriteLine(b.IsActive + " " + b.HasPendingChanges);
    }
}
