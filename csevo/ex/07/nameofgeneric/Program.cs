// 슬라이드 p7-v6-nameof-generic — 형식 매개변수의 이름, C# 6.0
using System;
using System.Collections.Generic;

class Repo<TItem>
{
    public string Describe()
    {
        return nameof(TItem) + " / " + typeof(TItem).Name;
    }
}

class App
{
    static string Show<T>(T value)
    {
        return nameof(T) + " = " + typeof(T).Name +
            ", " + nameof(value) + " = " + value;
    }

    static void Main()
    {
        Console.WriteLine(Show(42));
        Console.WriteLine(Show("hi"));
        Console.WriteLine(new Repo<DateTime>().Describe());
        Console.WriteLine(nameof(List<DateTime>) + " / " +
            typeof(List<DateTime>).Name);
    }
}
