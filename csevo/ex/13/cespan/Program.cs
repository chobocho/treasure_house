// 슬라이드 p13-v12-ce-span — 스팬 대상은 힙을 쓰지 않는다, C# 12
using System;
using System.Reflection;

class Program
{
    static int sink;
    static object keep;

    static void Consts()
    {
        ReadOnlySpan<int> r = [1, 2, 3];
        sink = r[2];
    }
    static void Vars()
    {
        for (int i = 0; i < 100; i++)
        {
            Span<int> s = [i, i + 1, i + 2];    // in a loop
            sink += s[2];
        }
    }
    static void Array() { int[] a = [1, 2, 3]; keep = a; }
    static long Bytes(Action a)
    {
        a();
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b0;
    }
    static void Main()
    {
        Console.WriteLine("ReadOnlySpan consts " + Bytes(Consts));
        Console.WriteLine("Span vars x100      " + Bytes(Vars));
        Console.WriteLine("int[] consts        " + Bytes(Array));
        Type pid = typeof(Program).Assembly
            .GetType("<PrivateImplementationDetails>");
        foreach (FieldInfo f in pid.GetFields(BindingFlags.Static
                                              | BindingFlags.NonPublic))
            Console.WriteLine(f.FieldType.Name + " " + f.Attributes);
    }
}
