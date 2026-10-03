// 슬라이드 p12-v11-rf-runtime — .NET 10 의 Span<T> 와 ref 필드, C# 11
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static void Main()
    {
        Console.WriteLine("ByRefFields: " +
            RuntimeFeature.IsSupported("ByRefFields"));
        foreach (FieldInfo f in typeof(Span<int>).GetFields(
            BindingFlags.Instance | BindingFlags.NonPublic))
            Console.WriteLine("Span<int>.{0} : {1} (IsByRef {2})",
                f.Name, f.FieldType, f.FieldType.IsByRef);
        Type br = typeof(object).Assembly.GetType("System.ByReference");
        Console.WriteLine("System.ByReference: " +
            (br == null ? "(none)" : br.ToString()));

        int local = 41;
        var one = new Span<int>(ref local);   // a span over a local
        one[0]++;
        Console.WriteLine("local = {0}, Length = {1}",
            local, one.Length);
    }
}
