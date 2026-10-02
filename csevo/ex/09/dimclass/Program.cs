// 슬라이드 p9-v8-dim-class — 기본 구현은 인터페이스로만, C# 8.0
using System;

interface IGreeter
{
    string Name { get; }
    void Hello() => Console.WriteLine("Hello, " + Name
        + " (this is " + GetType().Name + ")");
}

class Robot : IGreeter
{
    public string Name => "R2";
}

class App
{
    static void Main()
    {
        var r = new Robot();
        IGreeter g = r;
        g.Hello();                  // through the interface
        ((IGreeter)r).Hello();      // a cast works too
#if BAD
        r.Hello();                  // not a member of Robot
#endif
    }
}
