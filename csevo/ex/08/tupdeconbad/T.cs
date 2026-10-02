// 슬라이드 p8-v7-decon-bad — 분해가 거절되는 경우, C# 7.0
class Two
{
    public void Deconstruct(out int a, out int b) { a = 1; b = 2; }
}

class App
{
    static void Main()
    {
        var (c, d, e) = new Two();          // wrong arity
        var (f, g) = (1, 2, 3);             // tuple of three
        (int h, string i) = (1, 2);         // int is not a string
    }
}
