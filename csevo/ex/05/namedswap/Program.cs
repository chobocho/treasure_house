// 슬라이드 p5-v4-named-override — 이름도 정적 형식의 선언에서, C# 4.0
using System;

class Base
{
    public virtual void Move(int dx, int dy)
    {
        Console.WriteLine("Base dx=" + dx + " dy=" + dy);
    }
}

class Derived : Base
{
    public override void Move(int dy, int dx)    // names swapped
    {
        Console.WriteLine("Derived dx=" + dx + " dy=" + dy);
    }
}

class Program
{
    static void Main()
    {
        Derived d = new Derived();
        Base b = d;
        b.Move(dx: 1, dy: 2);
        d.Move(dx: 1, dy: 2);
    }
}
