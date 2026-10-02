// 슬라이드 p5-v4-dyn-expando-notify — 멤버가 생길 때 알림, C# 4.0
using System;
using System.ComponentModel;
using System.Dynamic;

class Program
{
    static void Main()
    {
        dynamic p = new ExpandoObject();
        INotifyPropertyChanged n = p;
        n.PropertyChanged +=
            delegate(object s, PropertyChangedEventArgs e)
        {
            Console.WriteLine("changed: " + e.PropertyName);
        };
        p.X = 1;
        p.X = 2;
        p.X = 2;
        p.Y = 3;
        Console.WriteLine(p.X + p.Y);
    }
}
