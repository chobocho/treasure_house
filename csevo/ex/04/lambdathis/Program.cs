// 슬라이드 p4-v3-lambda-this — this 만 잡은 람다의 대상, C# 3.0
using System;

class Greeter
{
    string name;
    public Greeter(string name) { this.name = name; }

    public Func<string> Make()
    {
        return () => "hi " + name;            // uses this.name
    }

    public bool TargetIsMe(Delegate d) { return d.Target == this; }
}

class App
{
    static void Main()
    {
        Greeter g = new Greeter("Ann");
        Func<string> f = g.Make();
        Console.WriteLine(f() + ", Target == g: " + g.TargetIsMe(f));
        Console.WriteLine("method on Greeter: "
            + (f.Method.DeclaringType == typeof(Greeter)));
    }
}
