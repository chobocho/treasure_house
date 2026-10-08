// 슬라이드 p1-design-overload — 파생 클래스의 후보가 먼저, C# 1.0
using System;

class Base
{
    public void F(int x) { Console.WriteLine("Base.F(int)"); }
}

class Derived : Base
{
    public void F(double x) { Console.WriteLine("Derived.F(double)"); }
}

class Program
{
    static void Main()
    {
        Derived d = new Derived();
        d.F(1);                    // int argument
        ((Base)d).F(1);
    }
}
