// 슬라이드 p3-v2-icomparable — IComparable<T> 와 정렬, C# 2.0
using System;
using System.Collections.Generic;

class Money : IComparable<Money>
{
    public readonly int Cents;
    public Money(int cents) { Cents = cents; }

    public int CompareTo(Money other)     // typed: no cast from object
    {
        return Cents.CompareTo(other.Cents);
    }

    public override string ToString() { return Cents + "c"; }
}

class App
{
    static void Main()
    {
        List<Money> xs = new List<Money>();
        xs.Add(new Money(250));
        xs.Add(new Money(99));
        xs.Add(new Money(1200));
        xs.Sort();                        // Comparer<Money>.Default
        foreach (Money m in xs)
        {
            Console.Write(m + " ");
        }
        Console.WriteLine();
        Console.WriteLine(xs[0] is IComparable);   // the 1.0 interface
    }
}
