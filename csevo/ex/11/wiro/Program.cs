// 슬라이드 p11-v10-wi-ro — with 가 쓸 수 없는 멤버, C# 10.0
using System;

struct Ticket
{
    public readonly int Id;                 // readonly field
    public string Seat { get; init; }       // init: allowed
    public string Gate { get; }             // get-only: not allowed
    public Ticket(int id) { Id = id; Seat = "A1"; Gate = "G3"; }
}

class App
{
    static void Main()
    {
        var t = new Ticket(7);
        var u = t with { Seat = "B2" };
        Console.WriteLine(u.Id + " " + u.Seat + " " + u.Gate);
#if BAD
        var v = t with { Id = 8, Gate = "G4" };
#endif
    }
}
