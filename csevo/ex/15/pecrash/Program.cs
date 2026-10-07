// 슬라이드 p15-v14-pe-crash — 인터페이스 이벤트와 partial, C# 14
using System;

interface INotify { event Action Ping; }

partial class A : INotify
{
#if FIX
    public partial event Action Pinged;    // another name
    event Action INotify.Ping
    {
        add => Pinged += value;
        remove => Pinged -= value;
    }
#else
    public partial event Action Ping;      // implements INotify.Ping
#endif
}

partial class A
{
#if FIX
    public partial event Action Pinged
#else
    public partial event Action Ping
#endif
    {
        add => Console.WriteLine("add");
        remove { }
    }
}

class Program
{
    static void Main() => ((INotify)new A()).Ping += () => { };
}
