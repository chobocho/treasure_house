// 슬라이드 p7-v6-autoinit-chain — this(…) 로 이어진 생성자, C# 6.0
using System;

class Order
{
    static int Next()
    {
        Console.WriteLine("  initializer");
        return 7;
    }

    public int Id { get; } = Next();
    public string Note { get; }

    public Order() : this("none")
    {
        Console.WriteLine("  Order()");
    }

    public Order(string note)
    {
        Note = note;
        Console.WriteLine("  Order(note)");
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine("new Order():");
        Order o = new Order();
        Console.WriteLine(o.Id + " " + o.Note);
    }
}
