// 슬라이드 p2-v1-static — 정적 멤버는 형식에 하나, C# 1.0
using System;

class Ticket
{
    static int issued;                      // one per type
    public readonly int Number;

    public Ticket()
    {
        issued++;
        Number = issued;
    }

    public static int Issued { get { return issued; } }

    public static Ticket Next() { return new Ticket(); }
}

class App
{
    static void Main()
    {
        Ticket a = new Ticket();
        Ticket b = Ticket.Next();
        Ticket c = Ticket.Next();
        Console.WriteLine(a.Number + " " + b.Number + " " + c.Number);
        Console.WriteLine("issued: " + Ticket.Issued);
    }
}
