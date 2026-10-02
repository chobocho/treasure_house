// 슬라이드 p8-v7_3-unmanaged — unmanaged 를 못 채우는 형식, C# 7.3
class C { }                       // a class
struct S { public string N; }     // a struct holding a reference
struct P<T> { public T A; }       // a generic struct

class U
{
    static void M<T>() where T : unmanaged { }

    static void Main()
    {
        M<C>();
        M<S>();
        M<P<int>>();              // C# 8.0 lets this one in
    }
}
