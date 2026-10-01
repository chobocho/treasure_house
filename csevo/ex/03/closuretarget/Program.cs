// 슬라이드 p3-v2-closure-target — 대리자의 Target 은 무엇인가, C# 2.0
using System;
using System.Runtime.CompilerServices;

delegate int D();

class App
{
    int field = 1;

    D NoCapture() { return delegate { return 0; }; }
    D UsesThis() { return delegate { return field; }; }
    D UsesLocal() { int x = 2; return delegate { return x; }; }

    static void Show(string name, D d, App app)
    {
        string kind;
        if (d.Target == null) kind = "null";
        else if (d.Target == (object)app) kind = "this";
        else if (d.Target.GetType().IsDefined(
                 typeof(CompilerGeneratedAttribute), false))
            kind = "generated";
        else kind = "other";
        Console.WriteLine(name + ": target " + kind
            + ", static " + d.Method.IsStatic);
    }

    static void Main()
    {
        App app = new App();
        Show("no capture", app.NoCapture(), app);
        Show("this only ", app.UsesThis(), app);
        Show("a local   ", app.UsesLocal(), app);
    }
}
