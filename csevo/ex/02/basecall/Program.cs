// 슬라이드 p2-v1-basecall — base 로 부르면 가상 호출이 아니다, C# 1.0
using System;

class Logger
{
    public virtual string Format(string msg) { return "[" + msg + "]"; }
}

class Stamped : Logger
{
    public override string Format(string msg)
    {
        return "1:" + base.Format(msg);       // non-virtual call
    }
}

class Loud : Stamped
{
    public override string Format(string msg)
    {
        return base.Format(msg.ToUpper()) + "!";
    }
}

class App
{
    static void Main()
    {
        Logger log = new Loud();
        Console.WriteLine(log.Format("ready"));
    }
}
