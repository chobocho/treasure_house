// 슬라이드 p2-v1-ctorvirt — 기반 생성자 안의 가상 호출, C# 1.0
using System;

class Base
{
    public Base() { Describe(); }    // virtual call, too early
    protected virtual void Describe() { }
}

class Derived : Base
{
    string fromInit = "set by initializer";
    string fromBody;
    int count;

    public Derived()
    {
        fromBody = "set by constructor body";
        count = 42;
    }

    protected override void Describe()
    {
        Console.WriteLine("fromInit = " + fromInit);
        string b = fromBody == null ? "null" : fromBody;
        Console.WriteLine("fromBody = " + b);
        Console.WriteLine("count    = " + count);
    }

    static void Main()
    {
        Derived d = new Derived();
        Console.WriteLine("-- after construction");
        d.Describe();
    }
}
