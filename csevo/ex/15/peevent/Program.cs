// 슬라이드 p15-v14-pe-event — partial 이벤트는 필드 꼴이 아니다, C# 14
using System;

partial class Door
{
    public partial event Action Opened, Closed;   // two events

    public void Open()
    {
#if VALUE
        Opened?.Invoke();                          // used as a value
#else
        opened?.Invoke();
#endif
    }
}

partial class Door
{
    Action opened;
    public partial event Action Opened
    {
        add => opened += value;
        remove => opened -= value;
    }
#if ADDONLY
    public partial event Action Closed { add { } }
#elif TWICE
    public partial event Action Closed;
#else
    public partial event Action Closed { add { } remove { } }
#endif
}

class Program
{
    static void Main()
    {
        var d = new Door();
        d.Opened += () => Console.WriteLine("opened");
        d.Open();
        Console.WriteLine(typeof(Door).GetFields(
            System.Reflection.BindingFlags.NonPublic |
            System.Reflection.BindingFlags.Instance).Length + " field");
    }
}
