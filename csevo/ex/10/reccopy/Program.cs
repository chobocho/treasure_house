// 슬라이드 p10-v9-rec-copy — 복사 생성자와 초기화자, C# 9.0
using System;

record Ticket(string Owner)
{
    static int next;
    public int Id { get; init; } = ++next;   // initializer
}

class App
{
    static void Main()
    {
        Ticket a = new Ticket("ann");
        Ticket b = new Ticket("bob");
        Ticket c = a with { Owner = "cat" };  // copy: no ++next
        Console.WriteLine(a);
        Console.WriteLine(b);
        Console.WriteLine(c);
        Console.WriteLine(new Ticket("dan").Id);
    }
}
