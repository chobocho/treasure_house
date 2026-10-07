// 슬라이드 p16-cp-waves — 웨이브마다 경고 하나, C# 14
using System;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;

static class Util { }
class point { public int x = 1; }               // wave 7

partial class Shape
{
    public partial string Name(int sides);
}

partial class Shape
{
    public partial string Name(int count) => count + " sides";  // 6
}

ref struct Holder
{
    public ref int R;                           // wave 10
    public int Read() => Unsafe.IsNullRef(ref R) ? -1 : R;
}

class Program
{
    static async Task<int> Work()
    {
        int local = 41;
        unsafe { int* p = &local; *p += 1; }    // wave 8
        await Task.Yield();
        return local;
    }

    static void Main()
    {
        object o = "x";
        Console.WriteLine(o is Util);           // wave 5
        Console.WriteLine(new Shape().Name(sides: 3));
        Console.WriteLine(new point().x);
        Console.WriteLine(new Holder().Read());
        Console.WriteLine(Work().Result);
    }
}
