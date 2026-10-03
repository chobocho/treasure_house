// 슬라이드 p12-v11-rf-span — ref 필드로 만든 작은 Span, C# 11
using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

readonly ref struct MySpan<T>
{
    readonly ref T _first;
    readonly int _length;

    public MySpan(T[] array)
    {
        _first = ref MemoryMarshal.GetArrayDataReference(array);
        _length = array.Length;
    }

    public MySpan(ref T one) { _first = ref one; _length = 1; }

    public int Length => _length;

    public ref T this[int i]
    {
        get
        {
            if ((uint)i >= (uint)_length)
                throw new IndexOutOfRangeException();
            return ref Unsafe.Add(ref _first, i);
        }
    }
}

class Program
{
    static void Main()
    {
        int[] data = { 1, 2, 3 };
        var s = new MySpan<int>(data);
        s[1] = 20;
        Console.WriteLine(string.Join(",", data) + " | " + s.Length);
        int local = 7;
        var one = new MySpan<int>(ref local);
        one[0]++;
        Console.WriteLine(local);
        try { one[1] = 0; }
        catch (IndexOutOfRangeException) { Console.WriteLine("i=1"); }
    }
}
