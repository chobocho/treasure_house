// 슬라이드 p5-v4-var-safety — out T 를 받는 자리에 두면, C# 4.0
interface IBox<out T>
{
    T Get();
    void Put(T item);
}

class Program
{
    static void Main()
    {
    }
}
