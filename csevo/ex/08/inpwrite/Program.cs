// 슬라이드 p8-v7_2-in-write — in 매개변수에 쓰기, C# 7.2
struct Big { public long A; }

class App
{
    static void Inc(ref long n) { n++; }

    static void M(in Big b)
    {
        b = default;      // the parameter itself
        b.A = 1;          // a field of it
        Inc(ref b.A);     // a writable ref to a field
    }

    static void Main()
    {
        M(in new Big());  // 'in' wants a variable
        M(in default(Big));
    }
}
