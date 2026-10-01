// 슬라이드 p3-v2-closure-lifetime — 잡힌 변수는 대리자만큼 산다, C# 2.0
using System;
using System.Runtime.CompilerServices;

delegate int D();

class App
{
    static D keep;                       // the delegate's only root
    static WeakReference weak;           // watches the array

    [MethodImpl(MethodImplOptions.NoInlining)]
    static void Make()
    {
        byte[] big = new byte[1000000];
        weak = new WeakReference(big);
        keep = delegate { return big.Length; };   // captures big
    }

    [MethodImpl(MethodImplOptions.NoInlining)]
    static void Collect(string when)
    {
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();
        Console.WriteLine(when + ": array alive " + weak.IsAlive);
    }

    static void Main()
    {
        Make();                          // Make has returned
        Collect("delegate kept");
        keep = null;
        Collect("delegate dropped");
    }
}
