// 슬라이드 p12-v11-rf-rules — ref 필드와 readonly, C# 11
using System;

ref struct RO                    // the proposal's ReadOnlyExample
{
    ref readonly int Field1;
    readonly ref int Field2;
    readonly ref readonly int Field3;

    public RO(int[] a)
    {
        Field1 = ref a[0];
        Field2 = ref a[1];       // a constructor may point it
        Field3 = ref a[2];
    }

    public void Uses(int[] a)
    {
        Field1 = ref a[1];       // ok: repoint
        Field2 = a[0];           // ok: write the value
#if BAD1
        Field1 = a[0];           // ref readonly: value is readonly
#endif
#if BAD2
        Field2 = ref a[0];       // readonly ref: cannot repoint
#endif
    }

    public int Sum => Field1 + Field2 + Field3;
}
#if BAD3
struct Plain { ref int F; }                  // not a ref struct
#endif
#if BAD4
readonly ref struct R2 { ref int F; }        // needs readonly ref
#endif
#if BAD5
ref struct Nest { ref Span<int> F; }         // ref to a ref struct
#endif

class Program
{
    static void Main()
    {
        int[] a = { 1, 2, 3 };
        var ro = new RO(a);
        Console.WriteLine(ro.Sum);
        ro.Uses(a);
        Console.WriteLine(ro.Sum + " | " + string.Join(",", a));
    }
}
