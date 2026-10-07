// 슬라이드 p15-v14-pe-rules — 정의 하나, 구현 하나, C# 14
using System;

partial class A
{
    public partial A();
    public partial event Action Done;
#if NOIMPL
    public partial A(int x);
#endif
#if STATIC
    static partial A();
#endif
}

partial class A
{
    public partial A() => Console.WriteLine("A()");
    public partial event Action Done { add { } remove { } }
#if NODEF
    public partial A(string s) { }
#endif
#if STATIC
    static partial A() { }
#endif
}

abstract partial class B
{
#if ABSTRACT
    public abstract partial event Action Gone;
#endif
}

#if NOTPARTIAL
class C
{
    public partial C();
    public partial C() { }
}
#endif

class Program
{
    static void Main() => new A();
}
