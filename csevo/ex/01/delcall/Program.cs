// 슬라이드 p1-design-del-call — 대리자 호출과 리플렉션 호출, C# 1.0
using System;
using System.Reflection;

delegate int Op(int a, int b);

class Calc
{
    public static int Add(int a, int b) { return a + b; }

    static long Now() { return GC.GetAllocatedBytesForCurrentThread(); }

    static void Main()
    {
        Op op = new Op(Add);
        MethodInfo m = typeof(Calc).GetMethod("Add");
        object[] args = new object[] { 3, 4 };
        int x = 0;
        object y = null;
        for (int i = 0; i < 1000; i++)          // warm up both paths
        { x = op(3, 4); y = m.Invoke(null, args); }

        long t = Now();
        for (int i = 0; i < 1000; i++) x = op(3, 4);
        long viaDelegate = Now() - t;

        t = Now();
        for (int i = 0; i < 1000; i++) y = m.Invoke(null, args);
        long viaInvoke = Now() - t;

        Console.WriteLine("delegate: " + x + ", allocated nothing: "
            + (viaDelegate == 0));
        Console.WriteLine("Invoke:   " + y + " (" + y.GetType().Name
            + "), allocated nothing: " + (viaInvoke == 0));
    }
}
