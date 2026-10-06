// 슬라이드 p14-v13-fk-shadow — field 라는 이름의 멤버, C# 13
using System;

class Counter
{
    private int field = 7;           // a member named 'field'

    public int A { get { return field; } }
    public int B { get { return this.field; } }
    public int C { get { return @field; } }
}

class Program
{
    static void Main()
    {
        var c = new Counter();
        Console.WriteLine(c.A + " " + c.B + " " + c.C);
    }
}
