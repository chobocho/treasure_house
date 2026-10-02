// 슬라이드 p7-v6-eb-reeval — => 와 { get; } = 의 차이, C# 6.0
using System;

class Ticket
{
    static int issued;

    static int Issue()
    {
        issued++;
        return issued;
    }

    public int Expr => Issue();           // runs on every read
    public int Init { get; } = Issue();   // runs once, at construction
}

class Program
{
    static void Main()
    {
        Ticket t = new Ticket();
        Console.WriteLine("Init: " + t.Init + " " + t.Init + " "
                          + t.Init);
        Console.WriteLine("Expr: " + t.Expr + " " + t.Expr + " "
                          + t.Expr);
        Console.WriteLine("Init: " + t.Init);
    }
}
