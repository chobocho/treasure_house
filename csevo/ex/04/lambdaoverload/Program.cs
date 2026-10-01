// 슬라이드 p4-v3-lambda-overload — 본문이 오버로드를 고른다, C# 3.0
using System;
using System.Collections.Generic;

class Detail
{
    public int UnitCount;
    public double UnitPrice;
}

class ItemList<T> : List<T>
{
    public int Sum(Func<T, int> selector)
    {
        Console.Write("Sum(Func<T,int>) → ");
        int sum = 0;
        foreach (T item in this) sum += selector(item);
        return sum;
    }

    public double Sum(Func<T, double> selector)
    {
        Console.Write("Sum(Func<T,double>) → ");
        double sum = 0;
        foreach (T item in this) sum += selector(item);
        return sum;
    }
}

class App
{
    static void Main()
    {
        ItemList<Detail> order = new ItemList<Detail>();
        order.Add(new Detail { UnitCount = 2, UnitPrice = 1.2 });
        order.Add(new Detail { UnitCount = 3, UnitPrice = 0.5 });
        Console.WriteLine(order.Sum(d => d.UnitCount));
        Console.WriteLine(order.Sum(d => d.UnitPrice * d.UnitCount));
    }
}
