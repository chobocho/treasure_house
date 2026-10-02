// 슬라이드 p5-v4-dyn-sig — object 와 dynamic 은 같은 시그니처, C# 4.0
class Program
{
    static void M(object o) { }
    static void M(dynamic d) { }

    static void Main()
    {
    }
}
