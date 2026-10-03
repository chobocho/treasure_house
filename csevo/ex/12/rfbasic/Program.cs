// 슬라이드 p12-v11-reffields — ref struct 의 ref 필드, C# 11
using System;

ref struct Ref<T>
{
    public ref T Value;                     // a ref field
    public Ref(ref T target) { Value = ref target; }
}

class Program
{
    static void Main()
    {
        int x = 1, y = 100;
        var r = new Ref<int>(ref x);
        r.Value = 5;                         // writes through to x
        Console.WriteLine("x = {0}", x);

        r.Value = ref y;                     // ref reassignment
        r.Value++;
        Console.WriteLine("x = {0}, y = {1}", x, y);

        int[] arr = { 10, 20, 30 };
        var e = new Ref<int>(ref arr[2]);
        e.Value *= 2;
        Console.WriteLine(string.Join(",", arr));
    }
}
