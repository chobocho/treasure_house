// 슬라이드 p10-v9-perf-runtime — 5장의 기능이 기대는 런타임, C# 9.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

class App
{
    static void Main()
    {
        Type[] ts = { typeof(SkipLocalsInitAttribute),
                      typeof(UnmanagedCallersOnlyAttribute),
                      typeof(CallConvCdecl), typeof(CallConvStdcall),
                      typeof(CallConvSuppressGCTransition) };
        foreach (Type t in ts)
            Console.WriteLine(t.FullName);
        Console.WriteLine("RuntimeFeature:");
        foreach (FieldInfo f in typeof(RuntimeFeature).GetFields())
        {
            if (!f.IsLiteral) continue;
            string key = (string)f.GetValue(null);
            bool on = RuntimeFeature.IsSupported(key);
            Console.WriteLine("  " + f.Name + " " + on);
        }
        Console.WriteLine(RuntimeInformation.ProcessArchitecture
            + ", IntPtr.Size " + IntPtr.Size);
    }
}
