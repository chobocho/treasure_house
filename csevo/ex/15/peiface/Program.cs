// 슬라이드 p15-v14-pe-iface — 인터페이스의 partial 이벤트, C# 14
using System;

partial interface IBus
{
    partial event Action Sent;                 // no 'public'
}

partial interface IBus
{
    partial event Action Sent
    {
        add => Console.WriteLine("IBus.add");
        remove { }
    }
}

class Bus : IBus
{
    public event Action Sent
    {
        add => Console.WriteLine("Bus.add");
        remove { }
    }
}

class Quiet : IBus { }

class Program
{
    static void Main()
    {
        IBus a = new Bus(), b = new Quiet();
        a.Sent += () => { };
        b.Sent += () => { };
        var add = typeof(IBus).GetEvent("Sent").AddMethod;
        Console.WriteLine(add.IsPublic + " " + add.IsVirtual);
    }
}
