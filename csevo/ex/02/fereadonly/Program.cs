// 슬라이드 p2-v1-foreach — 반복 변수는 읽기 전용, C# 1.0
class App
{
    static void Main()
    {
        int[] a = { 1, 2, 3 };
        foreach (int x in a)
        {
            x = x * 2;                   // cannot assign
        }
    }
}
