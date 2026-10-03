// 슬라이드 p12-v11-rq-rules — required 를 붙일 수 없는 곳, C# 11
using System;

public class Base
{
    public required int Ok { get; set; }
#if BAD1
    public required readonly int F1;              // readonly field
#endif
#if BAD2
    public required int P2 { get; }               // no setter
#endif
#if BAD3
    public required int P3 { get; internal set; } // setter less visible
#endif
#if BAD4
    protected required int F4;                    // less visible
#endif
#if BAD5
    public static required int S5 { get; set; }   // static
#endif
#if BAD6
    public required int this[int i] { get => i; set { } }
#endif
}

public interface I
{
#if BAD7
    required int P7 { get; set; }                 // interface
#endif
}

public class Derived : Base
{
#if BAD8
    public new int Ok { get; set; }               // hides Base.Ok
#endif
}

class Program
{
    static void Main() => Console.WriteLine(new Derived { Ok = 1 }.Ok);
}
