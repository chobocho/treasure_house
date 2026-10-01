// 슬라이드 p2-v1-opnames — 연산자 메서드를 이름으로 부르기, C# 1.0
class Vec
{
    public int X;
    public static Vec operator +(Vec a, Vec b) { a.X += b.X; return a; }
}

class App
{
    static void Main()
    {
        Vec v = Vec.op_Addition(new Vec(), new Vec());
        System.Console.WriteLine(v.X);
    }
}
